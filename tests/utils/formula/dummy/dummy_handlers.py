# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import time

from powerapi.handler import Handler
from powerapi.report import PowerReport


class ReportHandler(Handler):
    """
    Basic handler behaviour for a kind of Report
    """

    def _estimate(self, report):
        """
        Method that estimate the power consumption from an input report
        :param report: Input Report
        :return: List of PowerReport
        """
        socket_id = self.state.socket if self.state.socket is not None else -1

        metadata = report.metadata

        metadata['formula_name'] = self.state.actor.name
        metadata['socket'] = socket_id

        result_msg = PowerReport(timestamp=report.timestamp, sensor=report.sensor, target=report.target, power=42,
                                 metadata=metadata)
        return [result_msg]

    def handle(self, msg):
        """
        Process a report and send the result to the pusher actor
        :param powerapi.Report msg:  Received message
        """
        time.sleep(self.state.sleep_time)
        results = self._estimate(msg)
        for _, actor_pusher in self.state.pushers.items():
            for result in results:
                actor_pusher.send_data(result)
