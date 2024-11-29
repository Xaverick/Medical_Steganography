import React, { useState } from "react";
import axios from "axios";
import { Container, Row, Col, Form, Button, Alert, Spinner } from "react-bootstrap";

const App = () => {
    const [file, setFile] = useState(null);
    const [patientId, setPatientId] = useState("");
    const [data, setData] = useState("");
    const [output, setOutput] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleHideSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        const formData = new FormData();
        formData.append("file", file);
        formData.append("patient_id", patientId);
        formData.append("data", data);

        try {
            const res = await axios.post("http://127.0.0.1:5000/hide", formData);
            setOutput(res.data.file);
        } catch (err) {
            setError(err.response?.data?.error || "Something went wrong");
        } finally {
            setLoading(false);
        }
    };

    const handleRetrieveSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        const formData = new FormData();
        formData.append("file", file);

        try {
            const res = await axios.post("http://127.0.0.1:5000/retrieve", formData);
            setOutput(res.data.data);
        } catch (err) {
            setError(err.response?.data?.error || "Something went wrong");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container>
            <h1 className="text-center my-4">Medical Steganography</h1>
            <Row>
                <Col md={6}>
                    <h3>Hide Data</h3>
                    <Form onSubmit={handleHideSubmit}>
                        <Form.Group>
                            <Form.Label>File</Form.Label>
                            <Form.Control
                                type="file"
                                onChange={(e) => setFile(e.target.files[0])}
                            />
                        </Form.Group>
                        <Form.Group>
                            <Form.Label>Patient ID</Form.Label>
                            <Form.Control
                                type="text"
                                value={patientId}
                                onChange={(e) => setPatientId(e.target.value)}
                            />
                        </Form.Group>
                        <Form.Group>
                            <Form.Label>Data to Hide</Form.Label>
                            <Form.Control
                                as="textarea"
                                rows={3}
                                value={data}
                                onChange={(e) => setData(e.target.value)}
                            />
                        </Form.Group>
                        <Button variant="primary" type="submit" className="mt-3" disabled={loading}>
                            {loading ? <Spinner animation="border" size="sm" /> : "Hide Data"}
                        </Button>
                    </Form>
                </Col>

                <Col md={6}>
                    <h3>Retrieve Data</h3>
                    <Form onSubmit={handleRetrieveSubmit}>
                        <Form.Group>
                            <Form.Label>Stego File</Form.Label>
                            <Form.Control
                                type="file"
                                onChange={(e) => setFile(e.target.files[0])}
                            />
                        </Form.Group>
                        <Button variant="success" type="submit" className="mt-3" disabled={loading}>
                            {loading ? <Spinner animation="border" size="sm" /> : "Retrieve Data"}
                        </Button>
                    </Form>
                </Col>
            </Row>
            {output && (
                <Alert className="mt-4" variant="info">
                    <h4>Output:</h4>
                    {typeof output === "string" ? (
                        <p>{output}</p>
                    ) : (
                        <a href={`http://127.0.0.1:5000/${output}`} download>
                            Download File
                        </a>
                    )}
                </Alert>
            )}
            {error && <Alert variant="danger" className="mt-4">{error}</Alert>}
        </Container>
    );
};

export default App;
