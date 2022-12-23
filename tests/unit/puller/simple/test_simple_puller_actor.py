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
from time import sleep

import pytest

from powerapi.actor import NotConnectedException
from powerapi.actor.actor import InitializationException
from powerapi.message import StartMessage, \
    SimplePullerSendReportsMessage, PoisonPillMessage, UnknowMessageTypeException, Message, ErrorMessage
from powerapi.filter import Filter
from powerapi.puller.handlers import PullerInitializationException
from powerapi.report import HWPCReport
from powerapi.puller.simple.simple_puller_actor import SimplePullerActor

from powerapi.test_utils.dummy_actor import DummyActor
from tests.unit.actor.abstract_test_actor import AbstractTestActor, recv_from_pipe, is_actor_alive

NUMBER_OF_REPORTS_TO_SEND = 100
REPORT_TYPE_TO_BE_SENT = HWPCReport
ACTOR_NAME = 'simple-puller-actor'
DISPATCHER_NAME = 'fake_dispatcher'


def filter_rule(report):
    return True


class TestSimplePuller(AbstractTestActor):

    @pytest.fixture
    def started_fake_dispatcher(self, dummy_pipe_in):
        dispatcher = DummyActor(DISPATCHER_NAME, dummy_pipe_in, REPORT_TYPE_TO_BE_SENT)
        dispatcher.start()
        yield dispatcher
        if dispatcher.is_alive():
            dispatcher.terminate()

    @pytest.fixture
    def fake_filter(self, started_fake_dispatcher):
        fake_filter = Filter()
        fake_filter.filter(filter_rule, started_fake_dispatcher)
        return fake_filter

    @pytest.fixture
    def empty_filter(self):
        fake_filter = Filter()
        return fake_filter

    @pytest.fixture
    def actor(self, fake_filter):
        return SimplePullerActor(name=ACTOR_NAME, number_of_reports_to_send=NUMBER_OF_REPORTS_TO_SEND,
                                 report_type_to_send=REPORT_TYPE_TO_BE_SENT, report_filter=fake_filter)

    @pytest.fixture
    def actor_without_rules(self, empty_filter):
        return SimplePullerActor(name=ACTOR_NAME, number_of_reports_to_send=NUMBER_OF_REPORTS_TO_SEND,
                                 report_type_to_send=REPORT_TYPE_TO_BE_SENT, report_filter=empty_filter)

    @pytest.fixture
    def init_actor_without_rules(self, actor_without_rules):
        actor_without_rules.start()
        actor_without_rules.connect_data()
        actor_without_rules.connect_control()
        yield actor_without_rules
        if actor_without_rules.is_alive():
            actor_without_rules.terminate()
        actor_without_rules.socket_interface.close()

    @pytest.fixture
    def init_actor_without_terminate(self, actor):
        actor.start()
        actor.connect_data()
        actor.connect_control()
        return actor

    def test_create_simple_puller_with_router_without_rules_is_no_initialized(self, init_actor_without_rules,
                                                                              empty_filter):
        init_actor_without_rules.send_control(StartMessage('system'))

        assert not init_actor_without_rules.state.initialized

    def test_start_actor_send_reports_to_dispatcher(self,
                                                    started_actor,
                                                    started_fake_dispatcher,
                                                    dummy_pipe_out):
        count = 0
        report = REPORT_TYPE_TO_BE_SENT.create_empty_report()
        started_actor.send_data(SimplePullerSendReportsMessage('system', ACTOR_NAME))
        while count < NUMBER_OF_REPORTS_TO_SEND:
            sleep(1)
            assert recv_from_pipe(dummy_pipe_out, 2) == (DISPATCHER_NAME, report)
            count += 1

    def test_starting_actor_terminate_itself_after_poison_message_reception(self, init_actor_without_terminate):

        init_actor_without_terminate.send_control(PoisonPillMessage('simple-test-simple-puller'))
        assert not is_actor_alive(init_actor_without_terminate)
