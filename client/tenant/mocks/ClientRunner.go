// Copyright 2020 Northern.tech AS
//
//    Licensed under the Apache License, Version 2.0 (the "License");
//    you may not use this file except in compliance with the License.
//    You may obtain a copy of the License at
//
//        http://www.apache.org/licenses/LICENSE-2.0
//
//    Unless required by applicable law or agreed to in writing, software
//    distributed under the License is distributed on an "AS IS" BASIS,
//    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
//    See the License for the specific language governing permissions and
//    limitations under the License.

// Code generated by mockery v2.1.0. DO NOT EDIT.

package mocks

import (
	context "context"

	apiclient "github.com/mendersoftware/go-lib-micro/apiclient"

	mock "github.com/stretchr/testify/mock"

	tenant "github.com/mendersoftware/deviceauth/client/tenant"
)

// ClientRunner is an autogenerated mock type for the ClientRunner type
type ClientRunner struct {
	mock.Mock
}

// CheckHealth provides a mock function with given fields: ctx
func (_m *ClientRunner) CheckHealth(ctx context.Context) error {
	ret := _m.Called(ctx)

	var r0 error
	if rf, ok := ret.Get(0).(func(context.Context) error); ok {
		r0 = rf(ctx)
	} else {
		r0 = ret.Error(0)
	}

	return r0
}

// GetTenant provides a mock function with given fields: ctx, tid, client
func (_m *ClientRunner) GetTenant(ctx context.Context, tid string, client apiclient.HttpRunner) (*tenant.Tenant, error) {
	ret := _m.Called(ctx, tid, client)

	var r0 *tenant.Tenant
	if rf, ok := ret.Get(0).(func(context.Context, string, apiclient.HttpRunner) *tenant.Tenant); ok {
		r0 = rf(ctx, tid, client)
	} else {
		if ret.Get(0) != nil {
			r0 = ret.Get(0).(*tenant.Tenant)
		}
	}

	var r1 error
	if rf, ok := ret.Get(1).(func(context.Context, string, apiclient.HttpRunner) error); ok {
		r1 = rf(ctx, tid, client)
	} else {
		r1 = ret.Error(1)
	}

	return r0, r1
}

// VerifyToken provides a mock function with given fields: ctx, token, client
func (_m *ClientRunner) VerifyToken(ctx context.Context, token string, client apiclient.HttpRunner) (*tenant.Tenant, error) {
	ret := _m.Called(ctx, token, client)

	var r0 *tenant.Tenant
	if rf, ok := ret.Get(0).(func(context.Context, string, apiclient.HttpRunner) *tenant.Tenant); ok {
		r0 = rf(ctx, token, client)
	} else {
		if ret.Get(0) != nil {
			r0 = ret.Get(0).(*tenant.Tenant)
		}
	}

	var r1 error
	if rf, ok := ret.Get(1).(func(context.Context, string, apiclient.HttpRunner) error); ok {
		r1 = rf(ctx, token, client)
	} else {
		r1 = ret.Error(1)
	}

	return r0, r1
}
