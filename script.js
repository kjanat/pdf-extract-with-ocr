const uploadFile = async (file) => {
    let formData = new FormData();
    formData.append("file", file);

    const response = await fetch("http://localhost:5000/upload", {
        method: "POST",
        body: formData
    });

    const data = await response.json();
    console.log(data.text);  // Extracted text from the PDF
};
