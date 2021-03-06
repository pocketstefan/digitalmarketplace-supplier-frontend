from datetime import datetime
import re
import urllib.parse as urlparse

from flask import abort, current_app
from flask_login import current_user

from .frameworks import get_supplier_framework_info


def get_drafts(apiclient, framework_slug):
    drafts = apiclient.find_draft_services(
        current_user.supplier_id,
        framework=framework_slug
    )['services']

    complete_drafts = [draft for draft in drafts if draft['status'] in ('submitted', 'failed')]
    drafts = [draft for draft in drafts if draft['status'] == 'not-submitted']

    return drafts, complete_drafts


def get_lot_drafts(apiclient, framework_slug, lot_slug):
    drafts, complete_drafts = get_drafts(apiclient, framework_slug)
    return (
        [draft for draft in drafts if draft['lotSlug'] == lot_slug],
        [draft for draft in complete_drafts if draft['lotSlug'] == lot_slug]
    )


def count_unanswered_questions(service_attributes):
    unanswered_required, unanswered_optional = (0, 0)
    for section in service_attributes:
        for question in section.questions:
            if question.answer_required:
                unanswered_required += 1
            elif question.value in ['', [], None]:
                unanswered_optional += 1

    return unanswered_required, unanswered_optional


def is_service_associated_with_supplier(service):
    return service.get('supplierId') == current_user.supplier_id


def get_signed_document_url(uploader, document_path):
    url = uploader.get_signed_url(document_path)
    if url is not None:
        url = urlparse.urlparse(url)
        base_url = urlparse.urlparse(current_app.config['DM_ASSETS_URL'])
        return url._replace(netloc=base_url.netloc, scheme=base_url.scheme).geturl()


def parse_document_upload_time(data):
    match = re.search(r"(\d{4}-\d{2}-\d{2}-\d{2}\d{2})\..{2,3}$", data)
    if match:
        return datetime.strptime(match.group(1), "%Y-%m-%d-%H%M")


def get_next_section_name(content, current_section_id):
    if content.get_next_editable_section_id(current_section_id):
        return content.get_section(
            content.get_next_editable_section_id(current_section_id)
        ).name


def copy_service_from_previous_framework(data_api_client, content_loader, framework_slug, lot_slug, service_id):
    # Suppliers must have registered interest in a framework before they can edit draft services
    if not get_supplier_framework_info(data_api_client, framework_slug):
        abort(404)
    questions_to_copy = content_loader.get_metadata(framework_slug, 'copy_services', 'questions_to_copy')
    source_framework_slug = content_loader.get_metadata(framework_slug, 'copy_services', 'source_framework')

    previous_service = data_api_client.get_service(service_id)['services']
    if previous_service['lotSlug'] != lot_slug or previous_service['frameworkSlug'] != source_framework_slug \
            or previous_service['copiedToFollowingFramework']:
        abort(404)

    if not is_service_associated_with_supplier(previous_service):
        abort(404)

    data_api_client.copy_draft_service_from_existing_service(
        previous_service['id'],
        current_user.name,
        {
            'targetFramework': framework_slug,
            'status': 'not-submitted',
            'questionsToCopy': questions_to_copy
        },

    )
