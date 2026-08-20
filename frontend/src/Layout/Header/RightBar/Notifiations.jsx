import React, { Fragment } from 'react';
import { Bell } from 'react-feather';
import { LI, P, UL } from '../../../AbstractElements';

const Notifications = () => {
    return (
        <Fragment>
            <LI attrLI={{ className: 'onhover-dropdown' }} >
                <div className="notification-box">
                    <Bell />
                    <span className="dot-animated"></span></div>
                <UL attrUL={{ className: 'notification-dropdown onhover-show-div' }} >
                    <LI>
                        <P attrPara={{ className: 'f-w-700 m-0' }} >Notifications<span className="pull-right badge badge-primary badge-pill">0</span></P>
                    </LI>
                    <LI attrLI={{ className: 'dwella-notification-empty' }} >
                        <P attrPara={{ className: 'mb-0' }} >No new activity.</P>
                    </LI>
                </UL>
            </LI>
        </Fragment>
    );
};

export default Notifications;
