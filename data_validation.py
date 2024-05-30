import bleach

class Data_Validation:
    def clean_input(self, data):
        cleaned_data = bleach.clean(data)
        return cleaned_data
    
    # Checks if username and email are the same
    def check_match(self, input_1, input_2):
        return input_1 == input_2
