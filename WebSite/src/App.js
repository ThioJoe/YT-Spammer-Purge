import React from 'react';

import { Footer, Blog, Possibility, Features, WhatYTSP, Header } from './containers';
import { CTA, Navbar } from './components';

import './App.css';

const App = () => (
  <div className="App">
    <div className="gradient__bg">
      <Navbar />
      <Header />
    </div>
    <WhatYTSP />
    <Features />
    <Possibility />
    <CTA />
    <Blog />
    <Footer />
  </div>
);

export default App;
