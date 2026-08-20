import React from 'react';
import { Link } from 'react-router-dom';
import { Image } from '../../AbstractElements';
import logo from "/assets/images/logo/dwella-icon.png"

const SidebarLogo = () => {

  return (
    <div className="logo-icon-wrapper">
      <Link to={`/dashboard`}>
        <Image
          attrImage={{ className: 'img-fluid for-dark dwella-sidebar-logo', src: `${logo}`, alt: 'Dwella Suite' }} />
      </Link>
    </div>
  );
};

export default SidebarLogo;
