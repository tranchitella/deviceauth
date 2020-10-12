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

package orchestrator

import (
	"github.com/mendersoftware/deviceauth/model"
	"github.com/pkg/errors"
)

// DecomissioningReq contains request data of request to start decommissioning workflow
type DecommissioningReq struct {
	// Device ID
	DeviceId string `json:"device_id"`
	// Request ID
	RequestId string `json:"request_id"`
	// User authorization, eg. the value of Authorization header of incoming
	// HTTP request
	Authorization string `json:"authorization"`
}

// ProvisionDeviceReq contains request data of request to start provisioning workflow
type ProvisionDeviceReq struct {
	// Request ID
	RequestId string `json:"request_id"`
	// User authorization, eg. the value of Authorization header of incoming
	// HTTP request
	Authorization string `json:"authorization"`
	// Device
	Device model.Device `json:"device"`
}

// UpdateDeviceStatusReq contains request data of request to start update
// device status  workflow
type UpdateDeviceStatusReq struct {
	// Request ID
	RequestId string `json:"request_id"`
	// Device IDs
	Ids string `json:"device_ids"`
	// Tenant ID
	TenantId string `json:"tenant_id"`
	// new status
	Status string `json:"device_status"`
}

type DeviceLimitWarning struct {
	RequestID string `json:"request_id"`

	SenderEmail    string `json:"from"`
	RecipientEmail string `json:"to"`

	Subject          string `json:"subject"`
	Body             string `json:"body"`
	BodyHTML         string `json:"html"`
	RemainingDevices *uint  `json:"remaining_devices"`
}

func (dl *DeviceLimitWarning) Validate() error {
	const ErrMsgFmt = `invalid device limit request: missing parameter "%s"`
	if len(dl.SenderEmail) <= 0 {
		return errors.Errorf(ErrMsgFmt, "from")
	}
	if len(dl.RecipientEmail) <= 0 {
		return errors.Errorf(ErrMsgFmt, "to")
	}
	if len(dl.Subject) <= 0 {
		return errors.Errorf(ErrMsgFmt, "subject")
	}
	if len(dl.Body) <= 0 {
		return errors.Errorf(ErrMsgFmt, "body")
	}
	if len(dl.BodyHTML) <= 0 {
		return errors.Errorf(ErrMsgFmt, "html")
	}
	if dl.RemainingDevices == nil {
		return errors.Errorf(ErrMsgFmt, "remaining_devices")
	}
	return nil
}