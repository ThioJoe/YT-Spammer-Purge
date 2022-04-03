import React from 'react';
import ProTipImage from '../../assets/ProTip.svg';
import './ProTip.css';

const Possibility = () => (
  <div className="ytsp__ProTip section__padding" id="ProTip">
    <div className="ytsp__ProTip-image">
      <img src={ProTipImage} alt="ProTip" />
    </div>
    <div className="ytsp__ProTip-content">
      <h4>The Pro Tip</h4>
      <h1 className="gradient__text">
        Pro-Tip If This Seems Sketchy:
        <br />
        Limiting The App&apos;s Access
      </h1>
      <p>
        If you feel sketched out about giving the app the required high level
        permissions to your channel (very understandable), you could instead use
        the app in &apos;moderator mode&apos; (set in the config file). First,
        some context: When you grant access to another channel to be a moderator
        for your channel, they are able to mark comments for &apos;held for
        review&apos;, and this permission works through the API as well.
        <br /><br />
        Therefore, what you could do is create an blank dummy-google-account
        with nothing on it except a empty new channel. Then you can grant that
        channel permission to be a moderator, and use the app through the dummy
        moderator account. This way, you know that the app will never have the
        ability to do more than mark comments as held for review (which the app
        supports) on your main channel, and have no other access to your
        account&apos;s data. You just won&apos;t be able to ban the spammers
        through this app directly, but you can still remove/hide their comments
        instead of deleting them. Just make sure to create the google cloud API
        project on the dummy account instead.
        <br /><br />
        Read some additional details about &apos;moderator mode&apos; on the
        <a href="https://github.com/ThioJoe/YT-Spammer-Purge/wiki/Moderator-Mode-&-Limiting-Permissions"> wiki page here.
        </a>
      </p>
      <h4>Request Early Access to Get Started</h4>
    </div>
  </div>
);

export default Possibility;
