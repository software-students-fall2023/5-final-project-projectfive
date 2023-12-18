import { Link } from "react-router-dom";
import CreatePlan from "./CreatePlan"
import logo from '../img/logo.svg';
import '../App.css';

import { useEffect, useState } from "react";

import { List, Button, Form } from "antd";

function Home() {
  const [form] = Form.useForm();
  const [user, setUser] = useState(null)
  const [items, setItems] = useState([]);
  const [isModalVisible, setIsModalVisible] = useState(false);


  useEffect(()=>{
    setUser(localStorage.getItem('user'))
  },[])

  
  const handleComplete = (index) => {
    // 根据索引标记项目为已完成
    const updatedItems = [...items];
    updatedItems[index] = { ...updatedItems[index], title:`✅ ${updatedItems[index].title}`};
    setItems(updatedItems);
  };

  const handleDelete = (index) => {
    // 根据索引删除项目
    const updatedItems = [...items];
    updatedItems.splice(index, 1);
    setItems(updatedItems);
  };
  
    return ( 
      <div id="home" className="container">
        <div className="content">
          <div className='left'>
            <div className='header'>
              <h1 id="title">todo</h1>
              {user && <div className="user-name"> <Link >{user}</Link> </div>}
            </div>
            
            {user ?
              <div>
                <Button style={{marginBottom:10}} onClick={() => setIsModalVisible(true)} type="primary">create New Plan</Button>
                {items.length > 0 && (
                  <List
                    dataSource={items}
                    renderItem={(item, index) => (
                      <List.Item
                        actions={[
                          <Button
                            disabled={item.title.includes('✅')}
                            onClick={() => handleComplete(index)}
                            type="link"
                            key="complete"
                          >
                            Complete
                          </Button>,
                          <Button
                            onClick={() => handleDelete(index)}
                            type="link"
                            key="delete"
                          >
                            Delete
                          </Button>
                        ]}
                      >
                        {item.title}
                      </List.Item>
                    )}
                  />
                )}
                <CreatePlan 
                  items={items}
                  isModalVisible={isModalVisible} 
                  setIsModalVisible={setIsModalVisible} 
                  setItems={setItems}
                />
              </div>
              : <form>
                <Link className="btn" to="/Login">
                  <input id="Login" class="Login" type="submit" value="Login" />
                </Link>
                <Link to="/Signup">
                  <input id="Singup" class="Signup" type="submit" value="Signup" />
                </Link>
              </form>}

          </div>
          
          
          <div className='right'>
            <img src={logo} alt="home icon" id="hp"></img>
          </div>
        </div>
          
      </div>
    );
  }
  
  export default Home;