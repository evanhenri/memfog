import re
import os
import subprocess

from . import file_io, util


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
        return { field_name:field_obj.text for field_name,field_obj in self.__dict__.items() }

    def update_fields(self, args):
        for attr_id, attr_val in args.items():
            self.__dict__[attr_id].text = attr_val


class Interpreted(Raw):
    """
    Contains interpreted text from embedded instructions in the raw text (if any) for each UI field.
    Enables switching view modes without exiting UI.
    """
    def __init__(self, record):
        super(Interpreted, self).__init__(record)
        self.title = self.interpret(self.title)
        self.keywords = self.interpret(self.keywords)
        self.body = self.interpret(self.body)

    def interpret(self, text_field):
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

        for match in pattern.finditer(text_field.text):
            key, val = match.groups()
            val = ' '.join(map(os.path.expanduser, val.split()))
            text_field.instructions.append(tuple([key, val]))

            if key == 'PATH':
                file_content = file_io.str_from_file(val).expandtabs(tabsize=4)
                text_field.text = text_field.text.replace(match.group(0), file_content)

            elif key == 'EXEC':
                proc = subprocess.Popen(val, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                std_out, std_err = proc.communicate(timeout=5)
                proc.wait(timeout=5)
                proc_result = std_out.decode() + std_err.decode()
                text_field.text = text_field.text.replace(match.group(0), proc_result)

        # Even though all instructions are correctly interpretted, some of the embedded instructions still exist in
        # the text for the field in which the instruction exists in addition to the content interpreted from them.
        # Substitute any remaining instructions with empty string temporarily so they don't appear in UI
        text_field.text = re.sub(pattern, '', text_field.text)
        return text_field


class Data:
    def __init__(self, record):
        self.raw = Raw(record)
        self.interpreted = Interpreted(record)
        self.is_interpreted = self.raw.dump() != self.interpreted.dump()

    def update_interpreted_sources(self):
        """ Write changes made to interpreted PATH text to their source file """
        for field_name, field_obj in self.interpreted.__dict__.items():
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
        for field_name, field_obj in self.interpreted.__dict__.items():
            if not field_obj.is_interpreted() and field_obj.is_altered():
                self.raw.__dict__[field_name].text = field_obj.text

        # Any manual changes are now being reflected in the raw data fields. If a raw data field is detected as
        # being altered, add it to altered fields list and update context.record to contain the altered value
        for field_name, field_obj in self.raw.__dict__.items():
            if field_obj.is_altered():
                context.altered_fields.add(field_name)
                context.record.__dict__[field_name] = field_obj.text

        return context
