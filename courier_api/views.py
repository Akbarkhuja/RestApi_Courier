import json
import datetime
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ObjectDoesNotExist
from courier_api.models import Courier, Region, TimePeriod, Order, ForOrders

weights = {
    'foot': 10.0,
    'bike': 15.0,
    'car': 50.0
}


def compare_intervals(courier_intervals, delivery_intervals):
    for courier_interval in courier_intervals:
        intervals = courier_interval.split('-')
        start1 = datetime.datetime.strptime(intervals[0], "%H:%M")
        end1 = datetime.datetime.strptime(intervals[1], "%H:%M")

        for delivery_interval in delivery_intervals:
            intervals = delivery_interval.split('-')

            start2 = datetime.datetime.strptime(intervals[0], "%H:%M")
            end2 = datetime.datetime.strptime(intervals[1], "%H:%M")
            if start1 <= start2 <= end1 and start1 <= end2 <= end1:
                return True

    return False


@csrf_exempt
def post_courier(request):
    if request.method == 'POST':
        payload = json.loads(request.body)
        valid = []
        invalid = []

        for courier in payload['data']:
            _id = courier['courier_id']
            _type = courier['courier_type']
            regions = courier['regions']
            work_periods = courier['working_hours']

            if _type is None or _type == '':
                invalid.append(_id)
            elif regions is None or len(regions) == 0:
                invalid.append(_id)
            elif work_periods is None or len(work_periods) == 0:
                invalid.append(_id)

        if len(invalid):
            response = {'validation_error': {
                'couriers': [{'id': x} for x in invalid]
            }}
            return JsonResponse(response, status=400)
        else:
            for courier in payload['data']:
                result = Courier(id=courier['courier_id'], type=courier['courier_type'])
                result.save()

                for region in courier['regions']:
                    r, created = Region.objects.get_or_create(id=region)
                    result.regions.add(r)

                for period in courier['working_hours']:
                    p, created = TimePeriod.objects.get_or_create(period=period)
                    result.working_hours.add(p)
                valid.append(courier['courier_id'])

            response = {'couriers': [{'id': x} for x in valid]}
            return JsonResponse(response, status=201)


@csrf_exempt
def patch(request, courier_id):
    if request.method == 'PATCH':
        payload = json.loads(request.body)
        courier = Courier.objects.get(id=courier_id)

        if 'type' in payload:
            if payload['type'] is None or payload['type'] == '':
                return HttpResponseBadRequest()
            else:
                courier.type = payload['type']
        if 'regions' in payload:
            if payload['regions'] is None or len(payload['regions']) == 0:
                return HttpResponseBadRequest()
            else:
                courier.regions.clear()
                for region in payload['regions']:
                    r = Region(id=region)
                    r.save()
                    courier.regions.add(r)
        if 'working_hours' in payload:
            if payload['working_hours'] is None or len(payload['working_hours']) == 0:
                return HttpResponseBadRequest()
            else:
                courier.working_hours.clear()
                for period in payload['working_hours']:
                    p = TimePeriod(id=period)
                    p.save()
                    courier.working_hours.add(p)

        courier.save()
        result = {
            'courier_id': courier.id,
            'courier_type': courier.type,
            'regions': list(courier.regions.all().values_list('id', flat=True)),
            'working_hours': list(courier.working_hours.all().values_list('period', flat=True))
        }
        return JsonResponse(result, status=200)

    elif request.method == 'GET':
        courier = Courier.objects.get(id=courier_id)
        response = {
            'courier_id': courier.id,
            'courier_type': courier.type,
            'regions': list(courier.regions.all().values_list('id', flat=True)),
            'working_hours': list(courier.working_hours.all().values_list('period', flat=True))
        }
        return JsonResponse(response)


@csrf_exempt
def post_order(request):
    if request.method == 'POST':
        payload = json.loads(request.body)
        valid = []
        invalid = []

        for order in payload['data']:
            if order['weight'] is None:
                invalid.append(order['order_id'])
            elif order['region'] is None:
                invalid.append(order['order_id'])
            elif order['delivery_hours'] is None or not len(order['delivery_hours']):
                invalid.append(order['order_id'])

        if len(invalid):
            response = {'validation_error': {
                'orders': [{'id': x} for x in invalid]
            }}
            return JsonResponse(response, status=400)

        for order in payload['data']:
            result = Order(id=order['order_id'], weight=order['weight'], region=order['region'])
            result.save()

            for period in order['delivery_hours']:
                p = TimePeriod(period=period)
                p.save()
                result.delivery_time.add(p)

            valid.append(order['order_id'])

        response = {'orders': [{'id': x} for x in valid]}
        return JsonResponse(response, status=201)


@csrf_exempt
def get_order(request):
    if request.method == 'POST':
        payload = json.loads(request.body)
        courier_id = payload['courier_id']

        try:
            courier = Courier.objects.get(id=courier_id)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest()

        orders = Order.objects.filter(
            weight__lte=weights[courier.type],
            region__in=list(courier.regions.all().values_list('id', flat=True)),
            assigned=-1
        )

        for order in orders:    # can we do like this ???
            arg1 = list(courier.working_hours.all().values_list('period', flat=True))
            arg2 = list(order.delivery_time.all().values_list('period', flat=True))

            if compare_intervals(arg1, arg2):
                number, created = ForOrders.objects.get_or_create(id=order.id)
                courier.orders.add(number)

                order.assigned = courier.id

        response = {
            'orders':
                [{'id': x} for x in list(courier.orders.all().values_list('id', flat=True))]
        }
        return JsonResponse(response, status=200)


@csrf_exempt
def complete_delivery(request):
    if request.method == 'POST':
        payload = json.loads(request.body)
        courier_id = payload['courier_id']
        order_id = payload['order_id']

        try:
            order = Order.objects.get(id=order_id)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest()

        if order.assigned != courier_id:
            return HttpResponseBadRequest()
        
        try:
            courier = Courier.objects.get(id=courier_id)
        except ObjectDoesNotExist:
            return HttpResponseBadRequest()

        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute

        response = {'order_id': courier.id}
        return JsonResponse(response, status=200)
