import json
import os

import bravado
import pytest

from common import Device, DevAuthorizer, \
    device_auth_req, \
    clean_migrated_db, clean_db, mongo, cli, \
    management_api, internal_api, device_api, \
    tenant_foobar

import mockserver
import deviceadm
import inventory


def make_devices(device_api, devcount=1, tenant_token=""):
    print('device count to generate', devcount)

    url = device_api.auth_requests_url

    out_devices = []
    with deviceadm.run_fake_for_device(deviceadm.ANY_DEVICE) as server:
        for _ in range(devcount):
            dev = Device()
            da = DevAuthorizer(tenant_token=tenant_token)
            # poke devauth so that device appears
            rsp = device_auth_req(url, da, dev)
            assert rsp.status_code == 401
            out_devices.append((dev, da))

    return out_devices


@pytest.yield_fixture(scope='function')
def devices(device_api, management_api, clean_migrated_db, request):
    """Make unauthorized devices. The fixture can be parametrized a number of
    devices to make. Yields a list of tuples:
    (instance of Device, instance of DevAuthorizer)"""
    if not hasattr(request, 'param'):
        devcount = 1
    else:
        devcount = int(request.param)

    yield make_devices(device_api, devcount)


@pytest.yield_fixture(scope='function')
def tenant_foobar_devices(device_api, management_api, tenant_foobar, request):
    """Make unauthorized devices owned by tenant with ID 'foobar'. The fixture can
    be parametrized a number of devices to make. Yields a list of tuples:
    (instance of Device, instance of DevAuthorizer)
    """

    if not hasattr(request, 'param'):
        devcount = 1
    else:
        devcount = int(request.param)

    yield make_devices(device_api, devcount, tenant_token=tenant_foobar)


class TestDevice:

    def test_device_new(self, device_api, clean_migrated_db):
        d = Device()
        da = DevAuthorizer()

        with deviceadm.run_fake_for_device(d) as server:
            rsp = device_auth_req(device_api.auth_requests_url, da, d)
            assert rsp.status_code == 401

    def test_device_accept_nonexistent(self, management_api):
        try:
            management_api.accept_device('funnyid', 'funnyid')
        except bravado.exception.HTTPError as e:
            assert e.response.status_code == 404

    def test_device_reject_nonexistent(self, management_api):
        try:
            management_api.reject_device('funnyid', 'funnyid')
        except bravado.exception.HTTPError as e:
            assert e.response.status_code == 404

    def test_device_accept_reject_cycle(self, devices, device_api, management_api):
        d, da = devices[0]
        url = device_api.auth_requests_url

        dev = management_api.find_device_by_identity(d.identity)

        assert dev
        devid = dev.id

        print('found matching device with ID:', dev.id)
        aid = dev.auth_sets[0].id

        try:
            with inventory.run_fake_for_device_id(devid) as server:
                management_api.accept_device(devid, aid)
        except bravado.exception.HTTPError as e:
            assert e.response.status_code == 204

        # device is accepted, we should get a token now
        rsp = device_auth_req(url, da, d)
        assert rsp.status_code == 200

        da.parse_rsp_payload(d, rsp.text)

        assert len(d.token) > 0

        # reject it now
        try:
            management_api.reject_device(devid, aid)
        except bravado.exception.HTTPError as e:
            assert e.response.status_code == 204

        # device is rejected, should get unauthorized
        with deviceadm.run_fake_for_device(d) as server:
            rsp = device_auth_req(url, da, d)
            assert rsp.status_code == 401

    @pytest.mark.parametrize('devices', ['50'], indirect=True)
    def test_get_devices(self, management_api, devices):
        devcount = 50
        devs = management_api.list_devices()

        # try to get a maximum number of devices
        devs = management_api.list_devices(page=1, per_page=500)
        print('got', len(devs), 'devices')
        assert 500 >= len(devs) >= devcount

        # we have added at least `devcount` devices, so listing some lower
        # number of device should return exactly that number of entries
        plimit = devcount // 2
        devs = management_api.list_devices(page=1, per_page=plimit)
        assert len(devs) == plimit

    def test_get_device_limit(self, management_api):
        limit = management_api.get_device_limit()
        print('limit:', limit)
        assert limit.limit == 0

    @pytest.mark.xfail(reason='Not implemented yed, waiting for MEN-1486')
    @pytest.mark.parametrize('tenant_foobar_devices', ['5'], indirect=True)
    def test_device_limit_applied(self, management_api, internal_api,
                                  tenant_foobar_devices, tenant_foobar):
        """Verify that max accepted devices limit is indeed applied. Since device
        limits can only be set on per-tenant basis, use fixtures that setup
        tenant 'foobar' with devices and a token
        """
        expected = 2
        internal_api.put_max_devices_limit('foobar', expected)

        accepted = 0
        try:
            with inventory.run_fake_for_device_id(inventory.ANY_DEVICE):
                for dev, dev_auth in tenant_foobar_devices:
                    fdev = management_api.find_device_by_identity(dev.identity,
                                                                  Authorization=tenant_foobar)
                    aid = fdev.auth_sets[0].id
                    management_api.accept_device(fdev.id, aid,
                                                 Authorization=tenant_foobar)
                    accepted += 1
        except bravado.exception.HTTPError as e:
            assert e.response.status_code == 422
        finally:
            if accepted > expected:
                pytest.fail("expected only {} devices to be accepted".format(expected))

    def test_get_single_device_none(self, management_api):
        try:
            management_api.get_device(id='some-devid-foo')
        except bravado.exception.HTTPError as e:
            assert e.response.status_code == 404

    def test_get_device_single(self, management_api, devices):
        dev, _ = devices[0]

        # try to find our devices in all devices listing
        ourdev = management_api.find_device_by_identity(dev.identity)

        authdev = management_api.get_device(id=ourdev.id)
        assert authdev == ourdev

    def test_delete_device_nonexistent(self, management_api):
        # try delete a nonexistent device
        try:
            management_api.delete_device('some-devid-foo')
        except bravado.exception.HTTPError as e:
            assert e.response.status_code == 404

    def test_delete_device(self, management_api, devices):
        # try delete an existing device, verify decommissioning workflow was started
        # setup single device and poke devauth
        dev, _ = devices[0]
        ourdev = management_api.find_device_by_identity(dev.identity)
        assert ourdev

        # handler for orchestrator's job endpoint
        def decommission_device_handler(request):
            dreq = json.loads(request.body.decode())
            print('decommision request', dreq)
            # verify that devauth tries to decommision correct device
            assert dreq.get('device_id', None) == ourdev.id
            # test is enforcing particular request ID
            assert dreq.get('request_id', None) == 'delete_device'
            # test is enforcing particular request ID
            assert dreq.get('authorization', None) == 'Bearer foobar'
            return (200, {}, '')

        handlers = [
            ('POST', '/api/workflow/decommission_device', decommission_device_handler),
        ]
        with mockserver.run_fake(get_fake_orchestrator_addr(),
                                 handlers=handlers) as server:

            rsp = management_api.delete_device(ourdev.id, {
                'X-MEN-RequestID':'delete_device',
                'Authorization': 'Bearer foobar',
            })
            print('decommission request finished with status:',
                  rsp.status_code)
            assert rsp.status_code == 204

        found = management_api.find_device_by_identity(dev.identity)
        assert not found

    @pytest.mark.parametrize('devices', ['15'], indirect=True)
    def test_device_count_simple(self, devices, management_api):
        """We have 15 devices, each with a single auth set, verify that
        accepting/rejecting affects the count"""
        count = management_api.count_devices()

        assert count == 15

        pending_count = management_api.count_devices(status='pending')
        assert pending_count == 15

        # accept device[0] and reject device[1]
        for idx, (d, da) in enumerate(devices[0:2]):
            dev = management_api.find_device_by_identity(d.identity)

            assert dev
            devid = dev.id

            print('found matching device with ID:', dev.id)
            aid = dev.auth_sets[0].id

            try:
                with inventory.run_fake_for_device_id(devid) as server:
                    if idx == 0:
                        management_api.accept_device(devid, aid)
                    elif idx == 1:
                        management_api.reject_device(devid, aid)
            except bravado.exception.HTTPError as e:
                assert e.response.status_code == 204

        pending_count = management_api.count_devices(status='pending')
        assert pending_count == 13
        accepted_count = management_api.count_devices(status='accepted')
        assert accepted_count == 1
        rejected_count = management_api.count_devices(status='rejected')
        assert rejected_count == 1



def get_fake_orchestrator_addr():
    return os.environ.get('FAKE_ORCHESTRATOR_ADDR', '0.0.0.0:9998')

def get_fake_deviceadm_addr():
    return os.environ.get('FAKE_ADMISSION_ADDR', '0.0.0.0:9997')
