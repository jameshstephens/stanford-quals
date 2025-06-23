let allProblems = [];
let allTags = new Set();
let selectedTags = new Set();

// Initialize the application
function initializeApp() {
    // Use the embedded data
    allProblems = PROBLEMS_DATA;
    
    // Extract all unique tags
    allProblems.forEach(problem => {
        if (problem.tags && Array.isArray(problem.tags)) {
            problem.tags.forEach(tag => allTags.add(tag));
        }
    });
    
    // Sort tags alphabetically
    const sortedTags = Array.from(allTags).sort();
    
    // Create tag checkboxes
    createTagCheckboxes(sortedTags);
    
    // Initially show all problems
    displayProblems(allProblems);
    updateStats();
}

// Create tag checkboxes in the sidebar
function createTagCheckboxes(tags) {
    const tagList = document.getElementById('tagList');
    tagList.innerHTML = '';
    
    tags.forEach(tag => {
        const div = document.createElement('div');
        div.className = 'tag-item';
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `tag-${tag.replace(/\s+/g, '-').replace(/[^\w-]/g, '')}`;
        checkbox.value = tag;
        checkbox.addEventListener('change', handleTagChange);
        
        const label = document.createElement('label');
        label.htmlFor = checkbox.id;
        label.textContent = tag;
        
        div.appendChild(checkbox);
        div.appendChild(label);
        tagList.appendChild(div);
    });
}

// Handle tag checkbox changes
function handleTagChange(event) {
    const tag = event.target.value;
    
    if (event.target.checked) {
        selectedTags.add(tag);
    } else {
        selectedTags.delete(tag);
    }
    
    filterAndDisplayProblems();
    updateStats();
}

// Filter problems based on selected tags
function filterAndDisplayProblems() {
    let filteredProblems;
    
    if (selectedTags.size === 0) {
        // No tags selected, show all problems
        filteredProblems = allProblems;
    } else {
        // Show problems that have at least one of the selected tags
        filteredProblems = allProblems.filter(problem => 
            problem.tags && problem.tags.some(tag => selectedTags.has(tag))
        );
    }
    
    displayProblems(filteredProblems);
}

// Format title for better display
function formatTitle(title) {
    // Split by underscores and format each part
    const parts = title.split('_');
    if (parts.length >= 4) {
        const year = parts[0];
        const semester = parts[1];
        const session = parts[2];
        const problemNum = parts[3];
        return `${year} ${semester} - ${session.charAt(0).toUpperCase() + session.slice(1)} Problem ${problemNum}`;
    }
    return title;
}


// Display problems in the main content area
function displayProblems(problems) {
    const problemList = document.getElementById('problemList');
    
    if (problems.length === 0) {
        problemList.innerHTML = '<p>No problems match the selected tags.</p>';
        return;
    }
    
    problemList.innerHTML = problems.map(problem => `
        <div class="problem-item">
            <div class="problem-header">
                <h3>${formatTitle(problem.title)}</h3>
                <div class="problem-meta">
                    <span class="filename">${problem.filename}</span>
                </div>
            </div>
            <div class="problem-tags">
                ${problem.tags ? problem.tags.map(tag => `<span class="tag">${tag}</span>`).join(' ') : ''}
            </div>
            <div class="problem-content">
                ${problem.content}
            </div>
        </div>
    `).join('');
    
    // Re-render MathJax for the new content
    if (window.MathJax) {
        MathJax.typesetPromise([problemList]).catch(err => console.log('MathJax error:', err));
    }
}

// Update statistics display
function updateStats() {
    const problemCount = document.getElementById('problemCount');
    const selectedTagsCount = document.getElementById('selectedTagsCount');
    
    let filteredCount;
    if (selectedTags.size === 0) {
        filteredCount = allProblems.length;
    } else {
        filteredCount = allProblems.filter(problem => 
            problem.tags && problem.tags.some(tag => selectedTags.has(tag))
        ).length;
    }
    
    problemCount.textContent = `${filteredCount} problem${filteredCount !== 1 ? 's' : ''}`;
    selectedTagsCount.textContent = `${selectedTags.size} tag${selectedTags.size !== 1 ? 's' : ''} selected`;
}

// Select all tags
function selectAllTags() {
    const checkboxes = document.querySelectorAll('#tagList input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
        selectedTags.add(checkbox.value);
    });
    filterAndDisplayProblems();
    updateStats();
}

// Clear all tag selections
function clearAllTags() {
    const checkboxes = document.querySelectorAll('#tagList input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    selectedTags.clear();
    filterAndDisplayProblems();
    updateStats();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Set up button event listeners
    document.getElementById('selectAll').addEventListener('click', selectAllTags);
    document.getElementById('clearAll').addEventListener('click', clearAllTags);
    
    // Initialize the app
    initializeApp();
});