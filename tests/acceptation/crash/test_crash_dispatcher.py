# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.

# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.

# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.

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


"""
Test to interrupt the whole architecure after a crash that could hang the system

Architecture :
  - 1 puller (connected to MongoDB1 [collection test_hwrep], stream mode on)
  - 1 dispatcher (HWPC dispatch rule (dispatch by ROOT)
  - 1 Dummy Formula
  - 1 pusher (connected to MongoDB1 [collection test_result]

MongoDB1 content:
  - 1 HWPC Report


Scenario:
  - Launch the full architecture in a sub process
  - send a SIGKILL signal to the dispatcher to crash it
  - send a SIGTERM signal to the architecture process

Test if:
  - if the architecture process was terminated
"""
# pylint: disable=redefined-outer-name
# pylint: disable=unused-argument
# pylint: disable=unused-import

import time
import signal
import os
import pytest


from tests.utils.acceptation import MainProcess
from tests.utils.acceptation import get_actor_by_name, DISPATCHER_ACTOR_NAME
# noinspection PyUnresolvedReferences
from tests.utils.db.mongo import mongo_database
from tests.utils.formula.dummy import DummyFormulaActor
from tests.utils.report.hwpc import extract_rapl_reports_with_2_sockets


@pytest.fixture
def mongodb_content():
    """
        Retrieve 1 RAPL reports from a mongo database
    """
    return extract_rapl_reports_with_2_sockets(1)


@pytest.fixture
def main_process_crash_dispatcher():
    """
        Return the process to be used for testing.
        At the end of the test, the process will be stopped
    """
    p = MainProcessTestCrashDispatcher()
    p.start()
    time.sleep(1)
    yield p
    try:
        os.kill(p.pid, signal.SIGKILL)
    except OSError:
        pass


class MainProcessTestCrashDispatcher(MainProcess):
    """
    Process that run the global architecture and crash the dispatcher
    """

    def __init__(self):
        MainProcess.__init__(self, name='test_crash_dispatcher', sleep_time=1, formula_class=DummyFormulaActor)

    def run(self):
        MainProcess.run(self)

        dispatcher = get_actor_by_name(DISPATCHER_ACTOR_NAME, self.supervisor.supervised_actors)
        os.kill(dispatcher.pid, signal.SIGKILL)

        self.supervisor.join()


def test_crash_dispatcher(mongo_database, main_process_crash_dispatcher):
    """
        Check that the main process is actually stopped
    """
    if main_process_crash_dispatcher.is_alive():
        os.kill(main_process_crash_dispatcher.pid, signal.SIGTERM)
        main_process_crash_dispatcher.join(5)

        assert not main_process_crash_dispatcher.is_alive()

    assert True
