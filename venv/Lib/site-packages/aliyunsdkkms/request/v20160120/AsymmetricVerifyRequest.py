# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from aliyunsdkcore.request import RpcRequest
from aliyunsdkkms.endpoint import endpoint_data

class AsymmetricVerifyRequest(RpcRequest):

	def __init__(self):
		RpcRequest.__init__(self, 'Kms', '2016-01-20', 'AsymmetricVerify','kms')
		self.set_protocol_type('https')
		if hasattr(self, "endpoint_map"):
			setattr(self, "endpoint_map", endpoint_data.getEndpointMap())
		if hasattr(self, "endpoint_regional"):
			setattr(self, "endpoint_regional", endpoint_data.getEndpointRegional())


	def get_KeyVersionId(self):
		return self.get_query_params().get('KeyVersionId')

	def set_KeyVersionId(self,KeyVersionId):
		self.add_query_param('KeyVersionId',KeyVersionId)

	def get_Digest(self):
		return self.get_query_params().get('Digest')

	def set_Digest(self,Digest):
		self.add_query_param('Digest',Digest)

	def get_KeyId(self):
		return self.get_query_params().get('KeyId')

	def set_KeyId(self,KeyId):
		self.add_query_param('KeyId',KeyId)

	def get_Value(self):
		return self.get_query_params().get('Value')

	def set_Value(self,Value):
		self.add_query_param('Value',Value)

	def get_Algorithm(self):
		return self.get_query_params().get('Algorithm')

	def set_Algorithm(self,Algorithm):
		self.add_query_param('Algorithm',Algorithm)