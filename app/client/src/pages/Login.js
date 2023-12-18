import '../App.css';
import React, {useState} from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import Cookies from 'universal-cookie';


axios.defaults.withCredentials = true;

function Login() {
    const [data, setData] = useState({
      email: "",
      password: ""
    });
    const navigate = useNavigate();

    function handleLogin(e) {
      e.preventDefault();
      axios
      .post('http://localhost:443/api/login', data)
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
      <div id="login" className="login">
        <body>
          <h1 id="title">Login</h1>
          <div className="form1" id="form1">
            <form onSubmit={(e) => handleLogin(e)}>
            <input type="text" onChange={(e) => handleInput(e)} className="email" name="email" value={data.email} id="email" placeholder="Email"/> 
            <input type="text" onChange={(e) => handleInput(e)} className="password" name="password" value={data.password} id="password" placeholder="Password"/> 
            <input id="Login" className="Login" type="submit" value="Login"/> 
            </form>
          </div>
        </body>
      </div>
    );
  }
export default Login;