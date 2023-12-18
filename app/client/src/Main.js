import Home from './pages/Home';
import React from 'react';
import {
    BrowserRouter,
    Route,
    Routes,
  } from 'react-router-dom';


const Main = () => {
    return (
      <BrowserRouter>
      <Routes> {/* The Switch decides which component to show based on the current URL.*/}
        <Route index element={<Home/>}></Route>
      </Routes>
      </BrowserRouter>
    );
  };

export default Main;