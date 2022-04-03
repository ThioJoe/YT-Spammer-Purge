import React from 'react';
import Feature from '../../components/feature/Feature';
import './whatYTSP.css';

const WhatYTSP = () => (
  <div className="ytsp__whatytsp section__margin" id="wytsp">
    <div className="ytsp__whatytsp-feature">
      <Feature title="How to Download?" text="Click the Download link on the top, then on the latest release, under 'Assets' click to download 'YTSpammerPurge.exe'. The Tool is Available for Windows, Linux and Mac Devices. (You might have to click Assets to view the files for the release)" />
    </div>
    <div className="ytsp__whatytsp-heading">
      <h1 className="gradient__text">Usage Notes</h1>
      <p><a href="https://github.com/ThioJoe/YT-Spammer-Purge#purpose">Explore the Purpose</a></p>
    </div>
    <div className="ytsp__whatytsp-container">
      <Feature title="How to use the Script?" text="To use this script, you will need to obtain your own API credentials file by making a project via the Google Developers Console (aka 'Google Cloud Platform'). The credential file should be re-named client_secret.json and be placed in the same directory as this script." />
      <Feature title="What if the Script Freezes?" text="If it FREEZES while scanning, it is probably because you clicked within the command prompt window and entered 'selection mode' which pauses everything. To unfreeze it, simply right click within the window, or press the Escape key." />
      <Feature title="Warranty or Guarantee?" text="I'm a total amateur, so if something doesn't work I'll try to fix it. Therefore I OFFER NO WARRANTY OR GUARANTEE FOR THIS SCRIPT. USE AT YOUR OWN RISK. I tested it on my own and implemented some failcases as I could. You can Inspect the Code and Fix Them." />
    </div>
  </div>
);

export default WhatYTSP;
