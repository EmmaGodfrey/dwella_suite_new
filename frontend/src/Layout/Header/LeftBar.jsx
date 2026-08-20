import React, { Fragment, useContext, useState } from 'react';
import { Menu } from 'react-feather';
import { Link } from 'react-router-dom';
import { Image } from '../../AbstractElements';
import CheckContext from '../../_helper/Customizer';

const Leftbar = () => {

    const { toggleSidebar } = useContext(CheckContext);
    const [toggle, setToggle] = useState(false);


    const openCloseSidebar = () => {
        const nextToggle = !toggle;
        setToggle(nextToggle);
        toggleSidebar(nextToggle);
    };

    return (
        <Fragment>
            <div className="main-header-left">
                <div className="logo-wrapper">
                    <Link className="dwella-brand-link" to={`/dashboard`}>
                        <Image attrImage={{ className: 'img-fluid d-inline dwella-header-logo', src: `${('/assets/images/logo/dwella-wordmark.png')}`, alt: 'Dwella Suite' }} />
                    </Link>
                </div>
                <div className="toggle-sidebar" onClick={() => openCloseSidebar()}>
                    <Menu className="status_toggle middle" id="sidebar-toggle" />
                </div>
            </div>
        </Fragment >
    );
};

export default Leftbar;
