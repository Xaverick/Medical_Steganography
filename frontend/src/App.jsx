import React, { useState } from "react";
import axios from "axios";
import { Container, Row, Col, Form, Button, Spinner, Card, ProgressBar } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import { ToastContainer, toast } from "react-toastify"; // Import Toastify
import "react-toastify/dist/ReactToastify.css"; // Import the Toastify CSS

const App = () => {
    const [file, setFile] = useState(null);
    const [patientId, setPatientId] = useState("");
    const [data, setData] = useState("");
    const [output, setOutput] = useState(null);
    const [loadingHide, setLoadingHide] = useState(false); // separate loading for hide
    const [loadingRetrieve, setLoadingRetrieve] = useState(false); // separate loading for retrieve
    const [error, setError] = useState("");
    const [fileUrl, setFileUrl] = useState(null);

    const handleHideSubmit = async (e) => {
        e.preventDefault();
        setLoadingHide(true); // Show loader for hide data
        setError("");
        setOutput(null); // Clear previous output
        setFileUrl(null);
        const formData = new FormData();
        formData.append("file", file);
        formData.append("patient_id", patientId);
        formData.append("data", data);

        try {
            const res = await axios.post("http://127.0.0.1:5000/hide", formData);
            console.log("res", res);
            setOutput(res.data.file);
            setFileUrl(res.data.file_url);
            toast.success("Data hidden successfully!"); // Success toast
        } catch (err) {
            setError(err.response?.data?.error || "Something went wrong");
            toast.error(err.response?.data?.error || "Something went wrong"); // Error toast
        } finally {
            setLoadingHide(false); // Hide loader for hide data
        }
    };

    const handleRetrieveSubmit = async (e) => {
        e.preventDefault();
        setLoadingRetrieve(true); // Show loader for retrieve data
        setError("");
        setOutput(null); // Clear previous output
    
        // Create FormData and append the file to it
        const formData = new FormData();
        formData.append("file", file); // Append the file directly
    
        try {
            // Send the FormData with the file to the backend
            const res = await axios.post("http://127.0.0.1:5000/retrieve", formData);
    
            // Handle the response
            setOutput(res.data.data);
            setFileUrl(res.data.file_url);
            console.log("hello", res.data.file_url);
            toast.success("Data retrieved successfully!"); // Success toast
        } catch (err) {
            // Handle error
            setError(err.response?.data?.error || "Something went wrong");
            toast.error(err.response?.data?.error || "Something went wrong"); // Error toast
        } finally {
            // Set loading state to false
            setLoadingRetrieve(false); // Hide loader for retrieve data
        }
    };

    const handleViewImage = () => {
        if (fileUrl) {
            window.open(fileUrl, "_blank"); // Open the file in a new tab
        }
    };

    const downloadFile = async () => {
        const response = await fetch(fileUrl);
    
        // Check if the response is ok (status in the range 200-299)
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        try {
            // Convert the response to a Blob
            const blob = await response.blob();
            
            // Create a link element
            const link = document.createElement('a');
            
            // Create an object URL for the Blob
            link.href = window.URL.createObjectURL(blob);
            
            // Specify the filename for download
            link.download = 'encrypted_image' + fileUrl[-4]; 
            
            // Append to body and trigger download
            document.body.appendChild(link);
            link.click();
            
            // Clean up by removing the link
            document.body.removeChild(link);
            
            toast.success('File downloaded successfully!'); // Success toast
        } catch (error) {
            console.error('Error downloading file:', error);
            toast.error('Error downloading file'); // Error toast
        }
    };

    return (
        <Container>
            <h1 className="text-center my-4 text-primary">Medical Data Steganography</h1>
            <Row>
                <Col md={6}>
                    <Card className="shadow-sm mb-4">
                        <Card.Header className="bg-primary text-white">
                            <h3>Hide Data</h3>
                        </Card.Header>
                        <Card.Body>
                            <Form onSubmit={handleHideSubmit}>
                                <Form.Group>
                                    <Form.Label>File (Image or Audio)</Form.Label>
                                    <Form.Control
                                        type="file"
                                        onChange={(e) => setFile(e.target.files[0])}
                                        required
                                    />
                                </Form.Group>
                                <Form.Group>
                                    <Form.Label>Patient ID</Form.Label>
                                    <Form.Control
                                        type="text"
                                        value={patientId}
                                        onChange={(e) => setPatientId(e.target.value)}
                                        placeholder="Enter patient ID"
                                        required
                                    />
                                </Form.Group>
                                <Form.Group>
                                    <Form.Label>Data to Hide</Form.Label>
                                    <Form.Control
                                        as="textarea"
                                        rows={3}
                                        value={data}
                                        onChange={(e) => setData(e.target.value)}
                                        placeholder="Enter sensitive information"
                                        required
                                    />
                                </Form.Group>
                                <Button variant="primary" type="submit" className="mt-3 w-100" disabled={loadingHide}>
                                    {loadingHide ? <Spinner animation="border" size="sm" /> : "Hide Data"}
                                </Button>
                            </Form>
                        </Card.Body>
                    </Card>
                </Col>

                <Col md={6}>
                    <Card className="shadow-sm mb-4">
                        <Card.Header className="bg-success text-white">
                            <h3>Retrieve Data</h3>
                        </Card.Header>
                        <Card.Body>
                            <Form onSubmit={handleRetrieveSubmit}>
                                <Form.Group>
                                    <Form.Label>Stego File (Image or Audio)</Form.Label>
                                    <Form.Control
                                        type="file"
                                        onChange={(e) => setFile(e.target.files[0])}
                                        required
                                    />
                                </Form.Group>
                                <Button variant="success" type="submit" className="mt-3 w-100" disabled={loadingRetrieve}>
                                    {loadingRetrieve ? <Spinner animation="border" size="sm" /> : "Retrieve Data"}
                                </Button>
                            </Form>
                        </Card.Body>
                    </Card>
                    {output && (
    <div className="mt-4 text-center" style={{ backgroundColor: '#d4edda', padding: '20px', borderRadius: '8px' }}>
        <h3 className="mb-4" style={{ textAlign: 'center' }}>Encrypted Message:</h3> {/* Centered Heading */}
        {typeof output === "string" && output.endsWith(".png") ? (
            <div>
                <p>Encrypted image generated successfully!</p>
                <Button
                    variant="primary"
                    href={`http://127.0.0.1:5000/${output}`}
                    download
                >
                    Download Encrypted Image
                </Button>
            </div>
        ) : (
            <p>{output}</p>
        )}
    </div>
)}

                </Col>
            </Row>

            {loadingRetrieve && (
                <ProgressBar animated now={100} className="mt-3" label="Processing..." />
            )}

            {fileUrl && (
                <div className="mt-4">
                    <Button variant="primary" className="me-3" onClick={handleViewImage}>
                        View Encrypted Image /Audio
                    </Button>
                    <Button variant="secondary" onClick={downloadFile}>
                        Download Image/Audio
                    </Button>
                </div>
            )}

            {error && (
                toast.error(error) // Show error toast
            )}

            <ToastContainer /> {/* Add ToastContainer for showing toasts */}
        </Container>
    );
};

export default App;
