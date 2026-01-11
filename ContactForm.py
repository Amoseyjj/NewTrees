class ContactForm:
    count_id = 0

    def __init__(self, first_name, last_name, phone_number, email, message):
        ContactForm.count_id += 1
        self.__form_id = ContactForm.count_id
        self.__first_name = first_name
        self.__last_name = last_name
        self.__phone_number = phone_number
        self.__email = email
        self.__message = message

    def get_form_id(self):
        return self.__form_id

    def get_first_name(self):
        return self.__first_name

    def get_last_name(self):
        return self.__last_name

    def get_phone_number(self):
        return self.__phone_number

    def get_email(self):
        return self.__email

    def get_message(self):
        return self.__message

    def set_form_id(self, form_id):
        self.__form_id = form_id

    def set_first_name(self, first_name):
        self.__first_name = first_name

    def set_last_name(self, last_name):
        self.__last_name = last_name

    def set_phone_number(self, phone_number):
        self.__phone_number = phone_number

    def set_email(self, email):
        self.__email = email

    def set_message(self, message):
        self.__message = message

