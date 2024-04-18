frappe.pages['customer-document-tool'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Customer Document Tool',
		single_column: true
	});

	page.main.addClass("frappe-card");

	make_filters(page);

	$('<div class="tree"></div>').appendTo(page.body).append('<div class="no-result text-muted flex justify-center align-center" style="text-align: center; min-height: 250px;"><p>Select Customer to view the Documents.</p></div>');

}

function make_filters(page) {
	let customerField = page.add_field({
		label: __("Customer"),
		fieldname: "customer",
		fieldtype: "Link",
		options:"Customer",
		change() {
			if (page.fields_dict.customer.get_value()) {
          refresh_page(page);
      }
		}
	});
	page.fields_dict.customer.$input.on('change', function() {
		if (!page.fields_dict.customer.get_value()) {
				page.body.find(".tree").remove();
				$('<div class="tree"></div>').appendTo(page.body).append('<div class="no-result text-muted flex justify-center align-center" style="text-align: center; min-height: 250px;"><p>Select Customer to view the Documents.</p></div>');
		}
  });
}

function refresh_page(page){
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

					$(frappe.render_template("customer_document_tool",{categories})).appendTo(page.body);

					page.body.find(".tree-label").on("click", function() {
							$(".tree-node-toolbar").hide();
					    var toolbar = $(this).closest('.tree-link').next('.tree-node-toolbar');
					    toolbar.show();
					});

					page.body.find(".addDocument").on("click", function () {
						var sub_category = $(this).attr("sub-category");
						add_customer_document(customerName, sub_category)
					});

					page.body.find(".downloadDocument").on("click", function () {
						var document = $(this).attr("doc-id");
						window.open(document)
					});
				} else {
            // If no projects are found, append a message to the page body
						$('<div class="tree"></div>').appendTo(page.body).append('<div class="no-result text-muted flex justify-center align-center" style="text-align: center; min-height: 250px;"><p>No Documents found against this Customer.</p></div>');
        }
			}
	});

}

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
				}
			},
	});
}
