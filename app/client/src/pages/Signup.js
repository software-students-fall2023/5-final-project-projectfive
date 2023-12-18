import '../App.css';
import React, { useState } from 'react';
import axios from 'axios';
import Cookies from 'universal-cookie';
import { useNavigate } from 'react-router';

function Signup() {
  const navigate = useNavigate();
  const [data, setData] = useState({
    email: "",
    password: "",
    cpassword: ""
  });

  function handleSignup(e) {
    e.preventDefault();
    axios
    .post('/api/signup', data)
    .then((res) => {
        const status = res['data']['key'];

        console.log(status, res);
        if (res['data']['key'] === 'success') {
          console.log(data, 'cookie');
          const cookies = new Cookies();
          cookies.set('email', data['email']);
          navigate('/dashboard');
        }
      })
      .catch(err => {
        console.error(err);
      });
    }
  

  function handleInput(e) {
    const newData={...data};
    newData[e.target.id] = e.target.value;
    setData(newData);
  }
  

    return (
      <div id="Signup" className="Signup">
        <body>
          <h1 id="title">Signup</h1>
          <div className="form1" id="form1">
          <form onSubmit={(e) => handleSignup(e)}>
            <input type="text" onChange={(e) => handleInput(e)} class="email" name="email" id="email" placeholder="Email"/>  
            <input type="text" onChange={(e) => handleInput(e)} class="password" name="password" id="password" placeholder="Password"/>  
            <input type="text" onChange={(e) => handleInput(e)} class="cpassword" name="cpassword" id="cpassword" placeholder="Confirm Password"/>  
            <input id="Signup" class="Signup" type="submit" value="Signup"/> 
            </form>
          </div>
          
        </body>
      </div>
    );
  }
export default Signup;
