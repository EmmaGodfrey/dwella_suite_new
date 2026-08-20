
import React, { Fragment } from 'react';
import { useContext } from 'react';
import { UL } from '../../../AbstractElements';
import CustomizerContext from '../../../_helper/Customizer';
import AccountMenu from './AccountMenu';
import MoonLight from './MoonLight';
import Notifications from './Notifiations';

const Rightbar = () => {
    const { sidebarResponsive } = useContext(CustomizerContext);

    return (
        <Fragment>
            <div className="nav-right col pull-right right-menu p-0">
                <UL attrUL={{ className: `simple-list d-flex flex-row nav-menus ${sidebarResponsive ? 'open' : ''}` }} >
                    <Notifications />
                    <MoonLight />
                    <AccountMenu />
                </UL>
            </div>
        </Fragment>
    );
};

export default Rightbar;
