import React, { useState } from 'react';
import { RiMenu3Line, RiCloseLine } from 'react-icons/ri';
import logo from '../../logo.png';
import './navbar.css';

const Navbar = () => {
  const [toggleMenu, setToggleMenu] = useState(false);

  return (
    <div className="ytsp__navbar">
      <div className="ytsp__navbar-links">
        <div className="ytsp__navbar-links_logo">
          <img src={logo} />
        </div>
        <div className="ytsp__navbar-links_container">
          <p><a href="#home">Home</a></p>
          <p><a href="#wytsp">Usage</a></p>
          <p><a href="#features">Features</a></p>
          <p><a href="#ProTip">Pro Tip</a></p>
          <p><a href="#blog">Library</a></p>
        </div>
      </div>
      <div className="ytsp__navbar-sign">
        <p><a href="https://github.com/ThioJoe/YT-Spammer-Purge">Contribute</a></p>
        <button type="button"><a href="https://github.com/ThioJoe/YT-Spammer-Purge/releases/">Download</a></button>
      </div>
      <div className="ytsp__navbar-menu">
        {toggleMenu
          ? <RiCloseLine color="#fff" size={27} onClick={() => setToggleMenu(false)} />
          : <RiMenu3Line color="#fff" size={27} onClick={() => setToggleMenu(true)} />}
        {toggleMenu && (
        <div className="ytsp__navbar-menu_container scale-up-center">
          <div className="ytsp__navbar-menu_container-links">
            <p><a href="#home">Home</a></p>
            <p><a href="#wytsp">Usage</a></p>
            <p><a href="#features">Features</a></p>
            <p><a href="#ProTip">Pro Tip</a></p>
            <p><a href="#blog">Library</a></p>
          </div>
          <div className="ytsp__navbar-menu_container-links-sign">
            <p> <a href="https://github.com/ThioJoe/YT-Spammer-Purge">Contribute</a></p>
            <button type="button"> <a href="https://github.com/ThioJoe/YT-Spammer-Purge/releases/">Download</a></button>
          </div>
        </div>
        )}
      </div>
    </div>
  );
};

export default Navbar;
