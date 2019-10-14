"""Represents a structure to contain directions for how to parse and import
genomes into Phamerator."""

from pdm_utils.classes import eval
from pdm_utils.functions import basic




class GenomeTicket:

    # Initialize all attributes:
    def __init__(self):

        # Initialize all non-calculated attributes:
        self.id = None # Unique identifier
        self.type = "" # Add, Replace
        self.phage_id = ""
        self.run_mode = ""
        self.description_field = ""
        self.eval_flags = {} # Dictionary of evaluation flags.

        # Attributes used to populate Genome objects for
        # 'update', 'add', and 'replace' ticket types.
        self.data_retrieve = set() # Data that should be retrieved from PhagesDB.
        self.data_retain = set() # Data that should be retained from Phamerator.
        self.data_ticket = set() # Data to be added to genome from ticket.
        self.data_dict = {} # Original ticket data.

        # Used to check the structure of the ticket data.
        self.evaluations = []
        self._value_flag = False




    # When parsing data from an import ticket, some fields should be
    # lowercase regardless of the content, while other fields should
    # be lowercase only if they are set to 'none' or 'retrieve'.
    def set_type(self, value):
        """Set the ticket type.

        :param value: Value to be set as the type.
        :type value: str
        """
        self.type = value.lower()

    def set_description_field(self, value):
        """Set the description_field.

        :param value: Value to be set as the description_field.
        :type value: str
        """
        self.description_field = value.lower()

    def set_run_mode(self, value):
        """Set the run_mode.

        :param value: Value to be set as the run_mode.
        :type value: str
        """
        self.run_mode = value.lower()


    def set_value_flag(self, value):
        """Sets the flag if any attributes contain the specified 'value'.

        :param value:
            Indicates the value that should be searched within
            the attributes.
        :type value: str
        """
        if value in vars(self).values():
            self._value_flag = True
        else:
            self._value_flag = False

    def set_field_trackers(self):
        """Assigns ticket dictionary keys to specific sets."""
        for key in self.data_dict.keys():
            if self.data_dict[key] == "retrieve":
                self.data_retrieve.add(key)
            elif self.data_dict[key] == "retain":
                self.data_retain.add(key)
            else:
                self.data_ticket.add(key)


    # Evaluations




    def check_type(self, check_set, expect=True, eval_id=None):
        """Check that the type is valid.

        :param check_set: Set of reference types.
        :type check_set: set
        :param expect:
            Indicates whether the type is expected to be present
            in the check set.
        :type expect: bool
        :param eval_id: Unique identifier for the evaluation.
        :type eval_id: str
        """
        output = basic.check_value_expected_in_set(
                    self.type, check_set, expect)
        if output:
            result = "The field is populated correctly."
            status = "correct"
        else:
            result = "The field is not populated correctly."
            status = "error"
        definition = "Check if ticket type field is correctly populated."
        evl = eval.Eval(eval_id, definition, result, status)
        self.evaluations.append(evl)


    def check_phage_id(self, check_set, expect=True, eval_id=None):
        """Check that the phage_id is valid.

        :param check_set: Set of reference phage_ids.
        :type check_set: set
        :param expect:
            Indicates whether the phage_id is expected to be present
            in the check set.
        :type expect: bool
        :param eval_id: Unique identifier for the evaluation.
        :type eval_id: str
        """
        output = basic.check_value_expected_in_set(
                    self.phage_id, check_set, expect)
        if output:
            result = "The field is populated correctly."
            status = "correct"
        else:
            result = "The field is not populated correctly."
            status = "error"
        definition = "Check if phage_id field is correctly populated."
        evl = eval.Eval(eval_id, definition, result, status)
        self.evaluations.append(evl)


    def check_description_field(self, check_set, expect=True, eval_id=None):
        """Check that the description_field is valid.

        :param check_set: Set of reference description_field values.
        :type check_set: set
        :param expect:
            Indicates whether the description_field is expected to be present
            in the check set.
        :type expect: bool
        :param eval_id: Unique identifier for the evaluation.
        :type eval_id: str
        """
        output = basic.check_value_expected_in_set(
                    self.description_field, check_set, expect)
        if output:
            result = "The field is populated correctly."
            status = "correct"
        else:
            result = "The field is not populated correctly."
            status = "error"
        definition = "Check if description_field field is correctly populated."
        evl = eval.Eval(eval_id, definition, result, status)
        self.evaluations.append(evl)


    def check_run_mode(self, check_set, expect=True, eval_id=None):
        """Check that the run_mode is valid.

        :param check_set: Set of reference run_mode values.
        :type check_set: set
        :param expect:
            Indicates whether the run_mode is expected to be present
            in the check set.
        :type expect: bool
        :param eval_id: Unique identifier for the evaluation.
        :type eval_id: str
        """
        output = basic.check_value_expected_in_set(
                    self.run_mode, check_set, expect)
        if output:
            result = "The field is populated correctly."
            status = "correct"
        else:
            result = "The field is not populated correctly."
            status = "error"
        definition = "Check if run_mode field is correctly populated."
        evl = eval.Eval(eval_id, definition, result, status)
        self.evaluations.append(evl)

    def check_duplicate_id(self, set_of_duplicates, eval_id=None):
        """Check if the id is unique to this ticket by
        checking if it is found within a list of previously
        determined duplicate ids.

        :param set_of_duplicates: Set of reference duplicated values.
        :type set_of_duplicates: set
        :param eval_id: Unique identifier for the evaluation.
        :type eval_id: str
        """
        if self.id in set_of_duplicates:
            result = "The id is not unique to this ticket."
            status = "error"
        else:
            result = "The id is unique to this ticket"
            status = "correct"
        definition = "Check if the id is unique to this ticket."
        evl = eval.Eval(eval_id, definition, result, status)
        self.evaluations.append(evl)

    def check_duplicate_phage_id(self, set_of_duplicates, eval_id=None):
        """Check if the phage_id is unique to this ticket by
        checking if it is found within a list of previously
        determined duplicate phage_ids.

        :param set_of_duplicates: Set of reference duplicated values.
        :type set_of_duplicates: set
        :param eval_id: Unique identifier for the evaluation.
        :type eval_id: str
        """
        if self.phage_id in set_of_duplicates:
            result = "The phage_id is not unique to this ticket."
            status = "error"
        else:
            result = "The phage_id is unique to this ticket"
            status = "correct"
        definition = "Check if the phage_id is unique to this ticket."
        evl = eval.Eval(eval_id, definition, result, status)
        self.evaluations.append(evl)


    def check_compatible_type_and_annotation_status(self, eval_id=None):
        """Check if the ticket type and annotation_status are compatible.

        If the ticket type is 'add', then the annotation_status is not
        expected to be 'final'.
        If the ticket type is 'replace', then the annotation_status is
        not expected to be 'draft'.

        :param eval_id: Unique identifier for the evaluation.
        :type eval_id: str
        """
        if (self.type == "add" and self.annotation_status == "final"):
            result = "The ticket type indicates that a genome" + \
                     "with 'final' annotation_status will be added," + \
                     "which is not expected."
            status = "error"
        elif (self.type == "replace" and self.annotation_status == "draft"):
            result = "The ticket type indicates that a genome" + \
                     "with 'draft' annotation_status will be replaced," + \
                     "which is not expected."
            status = "error"
        else:
            result = "The ticket type and annotation_status are expected."
            status = "correct"
        definition = "Check if the ticket type and annotation_status" \
                     + " are compatible."
        evl = eval.Eval(eval_id, definition, result, status)
        self.evaluations.append(evl)


###
