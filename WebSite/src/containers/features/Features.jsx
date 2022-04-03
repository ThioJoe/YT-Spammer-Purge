import React from 'react';
import Feature from '../../components/feature/Feature';
import './features.css';

const featuresData = [
  {
    title: '15 Different Filtering Mothods ',
    text: 'Auto-Smart Mode, Sensitive-Smart Mode, Scan by Channel ID, Scan by Usernames, Scan Comment Text, Scan Usernames and Comment Text Simultaneously, ASCII Mode Scanning',
  },
  {
    title: '4 Different Scanning Modes',
    text: 'Scan a Video, Scan Recent Videos(Up to 5), Scan recent Comments across entire Channel for All videos',
  },
  {
    title: 'Recovery Mode and Match Samples',
    text: '"Recovery Mode" option to re-instate previously deleted comments. Displays "match samples" after printing comments list to easily spot false positives',
  },

];

const Features = () => (
  <div className="ytsp__features section__padding" id="features">
    <div className="ytsp__features-heading">
      <h1 className="gradient__text">The Features are gien below. Have some Ideas? Step into Community Today & Make your Ideas Happen by Contributing.</h1>
      <p>Detailed Info & Documentation → Visit the wiki <a href="https://github.com/ThioJoe/YT-Spammer-Purge/wiki">(Click Here)</a> for more detailed writeups on the program</p>
    </div>
    <div className="ytsp__features-container">
      {featuresData.map((item, index) => (
        <Feature title={item.title} text={item.text} key={item.title + index} />
      ))}
    </div>
  </div>
);

export default Features;
