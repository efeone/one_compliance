frappe.pages['customer-document-tool'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Customer Document Tool',
		single_column: true
	});

	page.main.addClass("frappe-card");

	make_filters(page);

	//Retrieve the selected customer from local storage that set from customer document
	var customer = localStorage.getItem('selected_customer');
	if (customer) {
		//if there is customer then refresh the pages
		refresh_page(page);
	} else {
		//if there is no customer selected, display a message to select a customer initially
		$('<div class="tree"></div>').appendTo(page.body).append('<div class="no-result text-muted flex justify-center align-center" style="text-align: center; min-height: 250px;"><p>Select Customer to view the Documents.</p></div>');
	}

}

function make_filters(page) {
	var customer = localStorage.getItem('selected_customer');

	// Add the customer field with the default value if it exists in local storage
	let customerField = page.add_field({
		label: __("Customer"),
		fieldname: "customer",
		fieldtype: "Link",
		options:"Customer",
		default: customer,
		change() {
			if (page.fields_dict.customer.get_value()) {
          refresh_page(page);
      }
		}
	});
	page.fields_dict.customer.$input.on('change', function() {
		if (!page.fields_dict.customer.get_value()) {
				// Remove the existing tree element to prevent repetition
				page.body.find(".tree").remove();
				//if there is no customer selected, display a message to select a customer
				$('<div class="tree"></div>').appendTo(page.body).append('<div class="no-result text-muted flex justify-center align-center" style="text-align: center; min-height: 250px;"><p>Select Customer to view the Documents.</p></div>');
		}
  });
}

function refresh_page(page){
	// Remove the selected value from local storage once retrieved
	localStorage.removeItem('selected_customer');
	page.body.find(".tree").remove();

	const customerName = page.fields_dict.customer.get_value();

	frappe.call({
			method: 'one_compliance.one_compliance.page.customer_document_tool.customer_document_tool.get_compliance_categories',
			args : {
				customer: customerName
			},
			callback: function(r) {
				if(r.message && r.message.length>0){
					var categories = r.message;

					// Render the values to html page
					$(frappe.render_template("customer_document_tool",{categories})).appendTo(page.body);

					// Display button once click on the sub category and documents
					page.body.find(".tree-label").on("click", function() {
							$(".tree-node-toolbar").hide();
					    var toolbar = $(this).closest('.tree-link').next('.tree-node-toolbar');
					    toolbar.show();
					});

					// Button action to add new document for existing customer
					page.body.find(".addDocument").on("click", function () {
						var sub_category = $(this).attr("sub-category");
						add_customer_document(customerName, sub_category)
					});

					// Button action to download the document
					page.body.find(".downloadDocument").on("click", function () {
						var document = $(this).attr("doc-id");
						window.open(document)
					});
				} else {
					// If no projects are found, append a message to the page body
					$('<div class="tree"></div>').appendTo(page.body).append('<div class="no-result text-muted flex justify-center align-center" style="text-align: center; min-height: 250px;"><p>No Documents found against this Customer. Create document from here.<br><button class="btn btn-default btn-xs tree-toolbar-button hidden-xs addDocument" customer="page.fields_dict.customer.get_value()">Create a new Task Document</button></p></div>');

					// Button action to create new customer document for a customer who hasn't document.
					page.body.find(".addDocument").on("click", function () {
						customer = page.fields_dict.customer.get_value()
						frappe.model.with_doctype('Customer Document', function() {
				        var newDoc = frappe.model.get_new_doc('Customer Document');
				        newDoc.customer = customer;
				        frappe.set_route('Form', 'Customer Document', newDoc.name);
				    });
					});
				}
			}
	});

}

// Function to add customer document.
function add_customer_document(customer, sub_category) {
	frappe.call({
		method: 'one_compliance.one_compliance.page.customer_document_tool.customer_document_tool.add_customer_document',
		args: {
			customer : customer,
			sub_category: sub_category
		},
		callback: function (r) {
				if (r) {
					frappe.set_route("Form", r.message.doctype, r.message.name);
					window.location.reload();
				}
			},
	});
}
