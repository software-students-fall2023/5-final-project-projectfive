
import Home from './pages/Home';
import Login from './pages/Login';
import Signup from './pages/Signup';
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
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
      </Routes>
      </BrowserRouter>
    );
  };

export default Main;