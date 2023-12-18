import '../App.css';
import React, {useState} from 'react';
import { Form, Input, Button } from "antd";

import request from '../utils';
import { useNavigate } from 'react-router-dom';


function Login() {
    
    const navigate = useNavigate();

    function handleLogin(data) {

      const formData = new FormData();
      formData.append('username', data.email);
      formData.append('password', data.password);
      request
        .post('/login', formData)
      .then((res) => {
        const status = res['data']['key'];

        console.log(status, res);
        if (res['data']['key'] === 'success') {
          localStorage.setItem('username', 'xx')
          navigate('/');
        }
      })
      .catch(err => {
        console.error(err);
      });
    }


    return ( 
      <div id="login" className="login">
        <body>
          <h1 id="title">Login</h1>
          
          <Form name="login-form" labelCol={{ span: 5 }} onFinish={handleLogin}>
              <Form.Item
                name="email"
                label=""
                rules={[{ required: true, message: "Please enter the Email" }]}
              >
              <Input placeholder="Enter the Email" />
              </Form.Item>

              <Form.Item
                name="password"
                label=""
                rules={[{ required: true, message: "Please enter the Password" }]}
              >
                <Input placeholder="Enter the Password" />
              </Form.Item>

            <Form.Item
             
            >
              <Button style={{ width:'100%'}} type="primary" htmlType="submit">
                Submit
              </Button>
            </Form.Item>

            </Form>
       
        </body>
      </div>
    );
  }
export default Login;