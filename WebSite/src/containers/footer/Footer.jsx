import React from 'react';
import ytspLogo from '../../logo.png';
import './footer.css';

const Footer = () => (
  <div className="ytsp__footer section__padding">
    <div className="ytsp__footer-heading">
      <h1 className="gradient__text">Do you want to know the Step by Step Installation of Youtube Spammer Purge? </h1>
    </div>

    <div className="ytsp__footer-btn">
      <p><a href="https://github.com/ThioJoe/YT-Spammer-Purge#installation">Installation</a></p>
    </div>

    <div className="ytsp__footer-links">
      <div className="ytsp__footer-links_logo">
        <img src={ytspLogo} alt="ytsp_logo" />
        <p>United States<br /> All Rights Reserved</p>
      </div>
      <div className="ytsp__footer-links_div">
        <h4>Links</h4>
        <p>Overons</p>
        <p>Social Media</p>
        <p>Counters</p>
        <p>Contact</p>
      </div>
      <div className="ytsp__footer-links_div">
        <h4>Company</h4>
        <p>Terms & Conditions </p>
        <p>Privacy Policy</p>
        <p>Contact</p>
      </div>
      <div className="ytsp__footer-links_div">
        <h4>Get in touch</h4>
        <p>United States</p>
        <p>00-12345678</p>
        <p>TJBusiness@thiojoe.com</p>
      </div>
    </div>

    <div className="ytsp__footer-copyright">
      <p>@2022 YTSP. All rights reserved.</p>
    </div>
  </div>
);

export default Footer;
