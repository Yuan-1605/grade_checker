/**
 * Grade Management System - Excel Import Script
 * 
 * Handles client-side validation and preview for Excel file imports
 */

document.addEventListener('DOMContentLoaded', function() {
    // Custom file input label update
    const fileInput = document.getElementById('file');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0] ? e.target.files[0].name : 'Choose file';
            const label = document.querySelector('.custom-file-label');
            if (label) {
                label.textContent = fileName;
            }
            
            // Validate file type
            validateExcelFile(this);
            
            // If SheetJS is available, create preview
            if (typeof XLSX !== 'undefined' && e.target.files[0]) {
                previewExcelFile(e.target.files[0]);
            }
        });
    }
    
    // Import form submission
    const importForm = document.getElementById('importForm');
    if (importForm) {
        importForm.addEventListener('submit', function(e) {
            const fileInput = document.getElementById('file');
            const classSelect = document.getElementById('class_id');
            
            if (!fileInput.files[0]) {
                e.preventDefault();
                alert('Please select an Excel file to import.');
                return false;
            }
            
            if (!classSelect.value) {
                e.preventDefault();
                alert('Please select a class for the imported grades.');
                return false;
            }
            
            if (!validateExcelFile(fileInput)) {
                e.preventDefault();
                return false;
            }
            
            // All validations passed
            return true;
        });
    }
});

/**
 * Validates the selected file is an Excel file
 * 
 * @param {HTMLInputElement} fileInput - The file input element
 * @returns {boolean} Whether the file is valid
 */
function validateExcelFile(fileInput) {
    if (!fileInput.files || fileInput.files.length === 0) {
        return false;
    }
    
    const file = fileInput.files[0];
    const fileName = file.name;
    const fileExt = fileName.substring(fileName.lastIndexOf('.')).toLowerCase();
    
    if (fileExt !== '.xlsx' && fileExt !== '.xls') {
        alert('Please select a valid Excel file (.xlsx or .xls)');
        fileInput.value = ''; // Clear the file input
        const label = document.querySelector('.custom-file-label');
        if (label) {
            label.textContent = 'Choose file';
        }
        return false;
    }
    
    return true;
}

/**
 * Creates a preview of the Excel file if SheetJS is available
 * 
 * @param {File} file - The selected Excel file
 */
function previewExcelFile(file) {
    // Check if SheetJS is available
    if (typeof XLSX === 'undefined') {
        console.warn('SheetJS (XLSX) not available. Excel preview disabled.');
        return;
    }
    
    const previewContainer = document.getElementById('excelPreview');
    if (!previewContainer) return;
    
    // Show loading indicator
    previewContainer.innerHTML = '<div class="text-center my-4"><i class="fas fa-spinner fa-spin mr-2"></i> Generating preview...</div>';
    
    // Use FileReader to read the file
    const reader = new FileReader();
    
    reader.onload = function(e) {
        try {
            // Parse the Excel data
            const data = new Uint8Array(e.target.result);
            const workbook = XLSX.read(data, { type: 'array' });
            
            // Get the first worksheet
            const firstSheetName = workbook.SheetNames[0];
            const worksheet = workbook.Sheets[firstSheetName];
            
            // Convert to JSON
            const jsonData = XLSX.utils.sheet_to_json(worksheet, { header: 1 });
            
            // Create preview table (displaying first 5 rows)
            const maxRows = Math.min(6, jsonData.length);
            
            let html = '<div class="mt-4">';
            html += '<h5>Excel Preview (First 5 rows):</h5>';
            html += '<div class="table-responsive">';
            html += '<table class="table table-sm table-bordered">';
            
            // Generate table header and rows
            for (let i = 0; i < maxRows; i++) {
                const row = jsonData[i];
                if (!row || row.length === 0) continue;
                
                html += '<tr>';
                for (let j = 0; j < row.length; j++) {
                    const cell = row[j] === undefined ? '' : row[j];
                    
                    if (i === 0) {
                        // Header row
                        html += `<th scope="col">${cell}</th>`;
                    } else {
                        html += `<td>${cell}</td>`;
                    }
                }
                html += '</tr>';
            }
            
            html += '</table>';
            html += '</div>';
            
            // Add note if there are more rows
            if (jsonData.length > 5) {
                html += `<p class="text-muted small">Showing 5 of ${jsonData.length} rows.</p>`;
            }
            
            // Add validation notes
            html += '<div class="alert alert-info mt-3">';
            html += '<h6>Import Validation:</h6>';
            html += '<ul class="mb-0">';
            
            // Check for required column format
            const firstColumnValid = jsonData[0] && (
                jsonData[0][0]?.toLowerCase() === 'student' ||
                jsonData[0][0]?.toLowerCase() === 'student name' ||
                jsonData[0][0]?.toLowerCase() === 'name' ||
                jsonData[0][0]?.toLowerCase() === 'student_name'
            );
            
            html += `<li>${firstColumnValid ? '✅' : '❌'} First column must be student names (labeled 'Student', 'Student Name', 'Name', or 'Student_Name')</li>`;
            html += '<li>Each additional column will be treated as a grade item</li>';
            html += '<li>Grades must be numeric values</li>';
            html += '</ul>';
            html += '</div>';
            
            html += '</div>';
            
            // Update the preview container
            previewContainer.innerHTML = html;
            
            // If invalid format, show warning
            if (!firstColumnValid) {
                alert('Warning: Your Excel file may not have the correct format. The first column should be labeled "Student", "Student Name", "Name", or "Student_Name".');
            }
            
        } catch (error) {
            console.error('Error parsing Excel file:', error);
            previewContainer.innerHTML = `<div class="alert alert-danger mt-3">Error generating preview: ${error.message}</div>`;
        }
    };
    
    reader.onerror = function() {
        previewContainer.innerHTML = '<div class="alert alert-danger mt-3">Error reading file</div>';
    };
    
    // Read the file as an array buffer
    reader.readAsArrayBuffer(file);
}
