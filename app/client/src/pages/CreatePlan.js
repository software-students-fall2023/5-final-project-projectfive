import {Form, Input, Modal, Select } from "antd";
import { useState } from "react";
const { TextArea } = Input

const CreatePlan = (props) =>{
    const { isModalVisible, setIsModalVisible, setItems, items } = props
    const [form] = Form.useForm();
    const [fileType, setFileType] = useState(null)
    const handleFormSubmit = () => {

        form.validateFields().then((values) => {
            const newItem = { title: values.title, content: values.content };
            setItems([...items, newItem]);
            form.resetFields();
            setFileType(null)
            setIsModalVisible(false);
        });
    };

    
    return (
        <Modal
            title="Create Plan"
            destroyOnClose={true}
            visible={isModalVisible}
            width={'45%'}
            
            onCancel={() => setIsModalVisible(false)}
            onOk={handleFormSubmit}
        >
            <Form form={form} labelCol={{ span: 5 }}>
                <Form.Item
                    name="title"
                    label="Title"
                    rules={[{ required: true, message: "Please enter the title" }]}
                >
                    <Input placeholder="Enter the title" />
                </Form.Item>

                <Form.Item
                    name="content"
                    label="Content"
                    rules={[{ required: true, message: "Please enter the content" }]}
                >
                    <TextArea rows={4} placeholder="Enter the content" />
                </Form.Item>

                <Form.Item name="fileType" label="File Type">
                    <Select onChange={value => setFileType(value)} options={[
                        { label: 'Save as draft', value: '0' }, { label: 'draft save as file', value: '1' }]}
                    ></Select>
                </Form.Item>

                {fileType === '1' &&<Form.Item name="locked" label="Is this a Locked plan?">
                    <Select options={[{ label: 'yes', value: '0' }, { label: 'no', value: '1' }]}
                    ></Select>
                </Form.Item>}

                {fileType === '1' &&<Form.Item name="visibility" label="Visibility of this plan">
                    <Select options={[{ label: 'Pubic', value: '0' }, { label: 'Private', value: '1' }]}
                    ></Select>
                </Form.Item>}

            </Form>
        </Modal>
        )
}

export default CreatePlan;