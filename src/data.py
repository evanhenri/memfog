import re
import os
import copy
import subprocess

from . import file_io


class TextField:
    """ Base class for UI text fields to inherit from """
    def __init__(self, text):
        self.text = text
        self.instructions = []
        self.starting_state = hash(self.text)

    def is_altered(self):
        return self.starting_state != hash(self.text)

    def is_interpreted(self):
        return len(self.instructions) > 0


class Title(TextField):
    def __init__(self, text):
        super(Title, self).__init__(text)

class Keywords(TextField):
    def __init__(self, text):
        super(Keywords, self).__init__(text)

class Body(TextField):
    def __init__(self, text):
        super(Body, self).__init__(text)


class Raw:
    """
    Contains raw, uninterpreted text for UI fields.
    Enables switching view modes without exiting UI.
    """
    def __init__(self, record):
        self.title = Title(record.title)
        self.keywords = Keywords(record.keywords)
        self.body = Body(record.body)

    def dump(self):
        return { field_name:field_obj.text for field_name,field_obj in vars(self).items() }

    def update_text(self, args):
        for attr_id, attr_val in args.items():
            vars(self)[attr_id].text = attr_val


class Interpreted(Raw):
    """
    Contains interpreted text from embedded instructions in the raw text (if any) for each UI field.
    Enables switching view modes without exiting UI.
    """
    def __init__(self, record):
        super(Interpreted, self).__init__(record)
        self.title = self.interpret_field(self.title)
        self.keywords = self.interpret_field(self.keywords)
        self.body = self.interpret_field(self.body)

    def interpret_field(self, field):
        """
        Parse text_field text, extract embedded instructions, and replace the instruction with the text
        interpretted from it.
        """
        pattern = re.compile(
        """                 # ?: denotes non-capture group - group that must be matched but excluded from the result
            (?:\[)          # Match \[
            (PATH|EXEC)     # Text between braces can be either PATH or EXEC
            (?:\]\()        # Match \]\(
            (.*?)           # >= 0 characters between parenthesis
            (?:\))          # Macth \)
        """, re.VERBOSE)

        for match in pattern.finditer(field.text):
            key, val = match.groups()
            val = ' '.join(map(os.path.expanduser, val.split()))
            field.instructions.append(tuple([key, val]))

            if key == 'PATH':
                file_content = file_io.str_from_file(val).expandtabs(tabsize=4)
                field.text = field.text.replace(match.group(0), file_content)

            elif key == 'EXEC':
                proc = subprocess.Popen(val, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                std_out, std_err = proc.communicate(timeout=5)
                proc.wait(timeout=5)
                proc_result = std_out.decode() + std_err.decode()
                field.text = field.text.replace(match.group(0), proc_result)

        # Even though all instructions are correctly interpretted, some of the embedded instructions still exist in
        # the text for the field in which the instruction exists in addition to the content interpreted from them.
        # Substitute any remaining instructions with empty string temporarily so they don't appear in UI
        field.text = re.sub(pattern, '', field.text)
        return field

    def refresh_from_sources(self, raw_data):
        """ Reintpret raw field text and and set to interpreted field to reflect any changes in linked sources """
        self.title = self.interpret_field(raw_data.title)
        self.keywords = self.interpret_field(raw_data.keywords)
        self.body = self.interpret_field(raw_data.body)


class Data:
    def __init__(self, record):
        self.raw = Raw(record)
        self.interpreted = Interpreted(record)
        self.is_interpreted = self.raw.dump() != self.interpreted.dump()

    def refresh_interpretation(self):
        """
        Update interpreted field to use values from re-interpretation of current raw field text.
        Deepcopy of raw fields required to stop to stop them from being changed to interpreted text.
        """
        self.interpreted.refresh_from_sources(copy.deepcopy(self.raw))
        self.is_interpreted = self.raw.dump() != self.interpreted.dump()

    def update_interpreted_sources(self):
        """ Write changes made to interpreted PATH text to their source file """
        for field_name, field_obj in vars(self.interpreted).items():
            for instruction_key, instruction_val in field_obj.instructions:
                if instruction_key == 'PATH':
                    file_io.str_to_file(instruction_val, field_obj.text)

    def update_record_context(self, context):
        """
        Determine which fields have been altered and add their field name to the context.
        Only fields that have been changed need to be updated in the database.
        Update context.record to mirror text from data fields.
        """
        # If a field in the interpretted data is altered but is not being interpreted, assign it's text value
        # to the corresponding raw data field
        for field_name, field_obj in vars(self.interpreted).items():
            if not field_obj.is_interpreted() and field_obj.is_altered():
                vars(self.raw)[field_name].text = field_obj.text

        # Any manual changes are now being reflected in the raw data fields. If a raw data field is detected as
        # being altered, add it to altered fields list and update context.record to contain the altered value
        for field_name, field_obj in self.raw.__dict__.items():
            if field_obj.is_altered():
                context.altered_fields.add(field_name)
                setattr(context.record, field_name, field_obj.text)

        return context
