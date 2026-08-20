import React, { Fragment, useContext, useState } from 'react';
import { Menu } from 'react-feather';
import { Link } from 'react-router-dom';
import { Image } from '../../AbstractElements';
import CheckContext from '../../_helper/Customizer';

const Leftbar = () => {

    const { mixLayout, toggleSidebar } = useContext(CheckContext);
    const [toggle, setToggle] = useState(false);


    const openCloseSidebar = () => {
        const nextToggle = !toggle;
        setToggle(nextToggle);
        toggleSidebar(nextToggle);
    };

    return (
        <Fragment>
            <div className="main-header-left">
                {mixLayout ?
                    <div className="logo-wrapper">
                            <Link to={`/dashboard`}>
                            <Image attrImage={{ className: 'img-fluid d-inline dwella-header-logo', src: `${('/assets/images/logo/eglabs-logo.png')}`, alt: 'EGLabs' }} />
                        </Link>
                    </div>
                    :
                    <div className="dark-logo-wrapper">
                        <Link to={`/dashboard`}>
                            <Image attrImage={{ className: 'img-fluid d-inline dwella-header-logo', src: `${('/assets/images/logo/eglabs-logo.png')}`, alt: 'EGLabs' }} />
                        </Link>
                    </div>
                }
                <div className="toggle-sidebar" onClick={() => openCloseSidebar()}>
                    <Menu className="status_toggle middle" id="sidebar-toggle" />
                </div>
            </div>
        </Fragment >
    );
};

export default Leftbar;
