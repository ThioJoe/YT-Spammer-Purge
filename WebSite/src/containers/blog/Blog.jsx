import React from 'react';
import Article from '../../components/article/Article';
import { blog01, blog02, blog03, blog04, blog05 } from './imports';
import './blog.css';

const Blog = () => (
  <div className="ytsp__blog section__padding" id="blog">
    <div className="ytsp__blog-heading">
      <h1 className="gradient__text">A lot is spoken about Youtube Spam Purge, We are blogging about it.</h1>
    </div>
    <div className="ytsp__blog-container">
      <div className="ytsp__blog-container_groupA">
        <Article imgUrl={blog01} date="Sep 26, 2021" text="Latest Demonstration Video. Let us exlore how to use it?" />
      </div>
      <div className="ytsp__blog-container_groupB">
        <Article imgUrl={blog02} date="Sep 26, 2021" text="I created an App that DESTROYS Scam Comments (Because YouTube would'nt)" />
        <Article imgUrl={blog03} date="Sep 26, 2021" text="Fixing what YouTube couldn't. - ThioJoe Spammer Purge" />
        <Article imgUrl={blog04} date="Sep 26, 2021" text="YouTube Needs to Fix This - Marques Brownlee" />
        <Article imgUrl={blog05} date="Sep 26, 2021" text="The YT-Spammer-Purge's Github Article by ThioJoe" />
      </div>
    </div>
  </div>
);

export default Blog;
