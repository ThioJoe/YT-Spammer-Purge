import React from 'react';
import people from '../../assets/people.png';
import ai from '../../assets/ai.png';
import './header.css';

const Header = () => (
  <div className="ytsp__header section__padding" id="home">
    <div className="ytsp__header-content">
      <h1 className="gradient__text">Let&apos;s Build Something amazing to Purge Youtube Spam Comments</h1>
      <p>Allows you to filter and search for spammer comments on your channel and other&apos;s channel(s) in many different ways AND delete/report them all at once</p>
      <div className="ytsp__header-content__input">
        <input type="text" placeholder="Follow this Link to Download" />
        <button type="button"><a href="https://github.com/ThioJoe/YT-Spammer-Purge/releases/">Download</a></button>
      </div>

      <div className="ytsp__header-content__people">
        <img src={people} />
        <p><a href="https://github.com/ThioJoe/YT-Spammer-Purge/graphs/contributors">The major Contributers for Youtube Spammer Purge Tool.</a></p>
      </div>
    </div>

    <div className="ytsp__header-image">
      <img src={ai} />
    </div>
  </div>
);

export default Header;
