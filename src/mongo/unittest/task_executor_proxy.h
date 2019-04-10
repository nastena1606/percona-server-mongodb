
/**
 *    Copyright (C) 2018-present MongoDB, Inc.
 *
 *    This program is free software: you can redistribute it and/or modify
 *    it under the terms of the Server Side Public License, version 1,
 *    as published by MongoDB, Inc.
 *
 *    This program is distributed in the hope that it will be useful,
 *    but WITHOUT ANY WARRANTY; without even the implied warranty of
 *    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *    Server Side Public License for more details.
 *
 *    You should have received a copy of the Server Side Public License
 *    along with this program. If not, see
 *    <http://www.mongodb.com/licensing/server-side-public-license>.
 *
 *    As a special exception, the copyright holders give permission to link the
 *    code of portions of this program with the OpenSSL library under certain
 *    conditions as described in each individual source file and distribute
 *    linked combinations including the program with the OpenSSL library. You
 *    must comply with the Server Side Public License in all respects for
 *    all of the code used other than as permitted herein. If you modify file(s)
 *    with this exception, you may extend this exception to your version of the
 *    file(s), but you are not obligated to do so. If you do not wish to do so,
 *    delete this exception statement from your version. If you delete this
 *    exception statement from all source files in the program, then also delete
 *    it in the license file.
 */

#pragma once

#include "mongo/base/disallow_copying.h"
#include "mongo/executor/task_executor.h"

namespace mongo {
namespace unittest {

/**
 * Proxy for the executor::TaskExecutor interface used for testing.
 */
class TaskExecutorProxy : public executor::TaskExecutor {
    MONGO_DISALLOW_COPYING(TaskExecutorProxy);

public:
    /**
     * Does not own target executor.
     */
    TaskExecutorProxy(executor::TaskExecutor* executor);
    virtual ~TaskExecutorProxy();

    executor::TaskExecutor* getExecutor() const;
    void setExecutor(executor::TaskExecutor* executor);

    virtual void startup() override;
    virtual void shutdown() override;
    virtual void join() override;
    virtual void appendDiagnosticBSON(BSONObjBuilder* builder) const override;
    virtual Date_t now() override;
    virtual StatusWith<EventHandle> makeEvent() override;
    virtual void signalEvent(const EventHandle& event) override;
    virtual StatusWith<CallbackHandle> onEvent(const EventHandle& event, CallbackFn work) override;
    virtual void waitForEvent(const EventHandle& event) override;
    virtual StatusWith<stdx::cv_status> waitForEvent(OperationContext* opCtx,
                                                     const EventHandle& event,
                                                     Date_t deadline) override;
    virtual StatusWith<CallbackHandle> scheduleWork(CallbackFn work) override;
    virtual StatusWith<CallbackHandle> scheduleWorkAt(Date_t when, CallbackFn work) override;
    virtual StatusWith<CallbackHandle> scheduleRemoteCommand(
        const executor::RemoteCommandRequest& request,
        const RemoteCommandCallbackFn& cb,
        const transport::BatonHandle& baton = nullptr) override;
    virtual void cancel(const CallbackHandle& cbHandle) override;
    virtual void wait(const CallbackHandle& cbHandle,
                      Interruptible* interruptible = Interruptible::notInterruptible()) override;
    virtual void appendConnectionStats(executor::ConnectionPoolStats* stats) const override;

private:
    // Not owned by us.
    executor::TaskExecutor* _executor;
};

}  // namespace unittest
}  // namespace mongo
