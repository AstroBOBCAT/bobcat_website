import os

from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from . import catalog_service as cat
from .models import BinaryModel, Candidate


def _safe_int(val, default, choices):
	try:
		n = int(val)
	except (TypeError, ValueError):
		return default
	return n if n in choices else default


def _copy_query(request, drop=None, **updates):
	q = request.GET.copy()
	if drop:
		for k in drop:
			q.pop(k, None)
	for k, v in updates.items():
		if v is None:
			q.pop(k, None)
		else:
			q[k] = str(v)
	return q


def _group_models_by_candidate(binary_qs):
	mapping = {}
	for bm in binary_qs:
		key = bm.candidate_name_id
		if not key:
			continue
		mapping.setdefault(key, []).append(bm)
	return mapping


def _sky_background_url():
	rel = 'mainpage/maps/pta_aitoff_bg.png'
	if not finders.find(rel):
		return ''
	try:
		from django.contrib.staticfiles.storage import staticfiles_storage

		return staticfiles_storage.url(rel)
	except Exception:
		return f'{settings.STATIC_URL}{rel}'


def mainpage(request):
	mode = request.GET.get('display', 'source')
	if mode not in ('source', 'model'):
		mode = 'source'

	page_size = _safe_int(request.GET.get('per_page'), 25, (10, 25, 50, 100, 200))
	try:
		page_num = int(request.GET.get('page', '1'))
	except (TypeError, ValueError):
		page_num = 1

	if mode == 'source':
		page_obj = cat.paginated_candidates_for_source_display(
			BinaryModel,
			Candidate,
			request.GET,
			page_num,
			page_size,
		)
	else:
		page_obj = cat.paginated_models_flat(
			BinaryModel,
			request.GET,
			page_num,
			page_size,
		)

	core_qs = cat.filtered_binary_queryset(BinaryModel, request.GET)
	by_cand = _group_models_by_candidate(core_qs)

	hlim_path = settings.BOBCAT_HLIM_TXT
	try:
		hlim_h, hlim_f = cat.read_hlim_two_column(hlim_path)
	except OSError:
		hlim_h, hlim_f = [], []

	sky_points = cat.sky_points_payload(BinaryModel, request.GET)
	gw_points = cat.gw_points_payload(BinaryModel, request.GET)

	sky_bg = _sky_background_url()
	bootstrap = {
		'sky': sky_points,
		'gw': gw_points,
		'hlim': {'h': hlim_h, 'f': hlim_f},
		'static': {
			'skyBg': bool(sky_bg),
			'skyBgUrl': sky_bg,
		},
	}

	columns_source = cat.SOURCE_COL_KEYS_DEFAULT
	columns_model = cat.MODEL_COL_KEYS_DEFAULT

	labels = cat.column_label_map()

	table_rows_source = []
	if mode == 'source':
		for cand in page_obj.object_list:
			bms = by_cand.get(cand.name, [])
			snip = cat.evidence_snippets_from_models(bms)
			table_rows_source.append(
				{
					'candidate': cand,
					'model_snippets': snip,
				},
			)

	table_rows_model = []
	if mode == 'model':
		for bm in page_obj.object_list:
			c = bm.candidate_name
			table_rows_model.append(
				{
					'bm': bm,
					'candidate': c,
					'ev_snip': cat.evidence_markup_for_binary_model(bm),
				},
			)

	q_export = request.GET.copy()
	export_csv_url = '?'.join((reverse('export-csv'), q_export.urlencode()))
	export_json_url = '?'.join((reverse('export-json'), q_export.urlencode()))

	prev_q = _copy_query(request, drop=('page',), page=max(page_obj.number - 1, 1))
	next_q = _copy_query(request, drop=('page',), page=min(page_obj.number + 1, page_obj.paginator.num_pages))

	keys_toolbar = {'display', 'page', 'per_page'}
	filters_open = any(
		(k not in keys_toolbar and str(v).strip())
		for k, v in request.GET.items()
	)

	ctx = {
		'page_obj': page_obj,
		'mode': mode,
		'bootstrap': bootstrap,
		'columns_source': columns_source,
		'columns_model': columns_model,
		'labels': labels,
		'all_source_cols': cat.ALL_SOURCE_COL_KEYS,
		'all_model_cols': cat.ALL_MODEL_COL_KEYS,
		'table_rows_source': table_rows_source,
		'table_rows_model': table_rows_model,
		'export_csv_url': export_csv_url,
		'export_json_url': export_json_url,
		'filters_open': bool(request.GET.get('filters')),
		'prev_qs': prev_q.urlencode(),
		'next_qs': next_q.urlencode(),
		'hlim_path_notice': os.path.isfile(hlim_path),
		'filters_open': filters_open,
	}
	return render(request, 'mainpage/main.html', ctx)


def export_csv_view(request):
	data = cat.csv_response_bytes(BinaryModel, request.GET)
	resp = HttpResponse(data, content_type='text/csv')
	resp['Content-Disposition'] = 'attachment; filename="bobcat_catalog.csv"'
	return resp


def export_json_view(request):
	payload = cat.export_json(BinaryModel, request.GET)
	resp = HttpResponse(payload, content_type='application/json')
	resp['Content-Disposition'] = 'attachment; filename="bobcat_catalog.json"'
	return resp


def stub_code(request):
	return render(
		request,
		'mainpage/stub.html',
		{
			'title': 'Code',
			'body': 'Links to analysis software and version control will go here.',
		},
	)


def stub_bobrefs(request):
	return render(
		request,
		'mainpage/stub.html',
		{
			'title': 'bobrefs',
			'body': 'Curated reference list for the collaboration (coming soon).',
		},
	)


def stub_classroom(request):
	return render(
		request,
		'mainpage/stub.html',
		{
			'title': 'BOBcat in the Classroom',
			'body': 'Educational materials and activities (coming soon).',
		},
	)
