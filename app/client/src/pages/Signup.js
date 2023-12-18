import '../App.css';
import React, { useState } from 'react';
import { Form, Input, Button, message } from "antd";

import request from '../utils';

// import Cookies from 'universal-cookie';
import { useNavigate } from 'react-router';

function Signup() {
  const navigate = useNavigate();
  
  function handleSignup(data) {
    
    if (data.password !== data.cpassword) {
      message.error('Password and Confirm Password do not match.');
      return;
    }

    const formData = new FormData();
    formData.append('username', data.email);
    formData.append('password', data.password);
    request
    .post('/register', formData)
    .then((res) => {
        const status = res['data']['key'];

        console.log(status, res);
        if (res['data']['key'] === 'success') {
          console.log(data, 'cookie');
          // const cookies = new Cookies();
          // cookies.set('email', data['email']);
          navigate('/dashboard');
        }
      })
      .catch(err => {
        console.error(err);
      });
    }
  

  

    return (
      <div id="Signup" className="Signup">
        <body>
          <h1 id="title">Sign up</h1>
          <div className="form1" id="form1">

            <Form name="login-form" labelCol={{ span: 5 }} onFinish={handleSignup}>
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
                name="cpassword"
                label=""
                rules={[{ required: true, message: "Please enter the Confirm Password" }]}
              >
                <Input placeholder="Confirm Password" />
              </Form.Item>

              <Form.Item

              >
                <Button style={{ width: '100%' }} type="primary" htmlType="submit">
                  Signup
                </Button>
              </Form.Item>

            </Form>
          
          </div>
          
        </body>
      </div>
    );
  }
export default Signup;
