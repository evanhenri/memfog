from . import data, user

class Memory:
    def __init__(self):
        self.title = ''
        self.keywords = ''
        self.body = ''
        self.search_score = 0

    def __gt__(self, other_memory):
        return self.search_score > other_memory.search_score

    def get_backup(self):
        return {k:v for k,v in self.__dict__.items() if k != 'search_score'}

    def edit_menu(self):
        while True:
            print('1) Edit Title\n2) Edit Keywords\n3) Edit Body')
            selection = input('> ')

            if data.is_valid_input(selection):
                selection = int(selection)
                options = {
                    1:self.update_title,
                    2:self.update_keywords,
                    3:self.update_body,
                }

                if selection not in options:
                    break
                else:
                    options[selection]()
            else:
                break

    def make_set(self):
        m_data = ' '.join([self.title, self.keywords])
        return set(data.standardize(m_data))

    def update_title(self):
        self.title = user.prefilled_input('Title: ', self.title)

    def update_keywords(self):
        self.keywords = user.prefilled_input('Keywords: ', self.keywords)

    def update_body(self):
        self.body = user.prefilled_input('Body: ', self.body)