from flask_login import login_required, current_user
from flask import render_template

from app.main import main
from .. import data_api_client


@main.route('/dashboard')
@login_required
def dashboard():
    template_data = main.config['BASE_TEMPLATE_DATA']
    suppliers_services = data_api_client.find_services(
        supplier_id=current_user.supplier_id
    )

    return render_template(
        "services/dashboard.html",
        services=suppliers_services["services"],
        **template_data), 200


@main.route('/services/<string:service_id>')
@login_required
def services(service_id):
    template_data = main.config['BASE_TEMPLATE_DATA']
    return render_template(
        "services/services.html",
        service_id=service_id,
        **template_data), 200