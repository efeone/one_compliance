def get_event_participant_custom_fields():
	'''
		Method to get custom fields for Event Participants doctype
	'''
	return {
		"Event Participants": [
			{
				"fieldname": "custom_participant_name",
				"fieldtype": "Data",
				"in_list_view": 1,
				"insert_after": "email",
				"label": "Participant Name",
			}
		]
	}
