/**
 * dropdown-utils.js
 * =================
 * 
 * Searchable dropdown functionality for team selection
 */

import { NBA_TEAMS, TEAM_ABBREVIATIONS } from './constants.js';

// Initialize all searchable dropdowns
export function initializeSearchableDropdowns() {
  const teamSelects = document.querySelectorAll('.team-select');
  
  teamSelects.forEach(select => {
    // Add search functionality to each dropdown
    makeSelectSearchable(select);
  });
}

// Convert regular select to searchable dropdown
function makeSelectSearchable(selectElement) {
  const wrapper = selectElement.parentElement;
  const selectId = selectElement.id;
  const currentValue = selectElement.value;
  
  // Create search input
  const searchInput = document.createElement('input');
  searchInput.type = 'text';
  searchInput.className = 'team-search-input';
  searchInput.placeholder = `Search ${selectId === 'homeTeam' ? 'Home' : 'Away'} Team...`;
  searchInput.value = currentValue;
  
  // Create dropdown list
  const dropdownList = document.createElement('div');
  dropdownList.className = 'team-dropdown-list';
  
  // Hide original select and add new elements
  selectElement.style.display = 'none';
  wrapper.appendChild(searchInput);
  wrapper.appendChild(dropdownList);
  
  let highlightedIndex = -1;
  
  // Populate dropdown with all teams initially
  function populateDropdown(teams = NBA_TEAMS) {
    dropdownList.innerHTML = '';
    
    teams.forEach((team, index) => {
      const item = document.createElement('div');
      item.className = 'team-dropdown-item';
      item.textContent = team;
      item.dataset.value = team;
      item.dataset.index = index;
      
      item.addEventListener('click', () => {
        selectTeam(team);
      });
      
      dropdownList.appendChild(item);
    });
  }
  
  // Select a team
  function selectTeam(teamName) {
    searchInput.value = teamName;
    selectElement.value = teamName;
    dropdownList.classList.remove('show');
    highlightedIndex = -1;
    
    // Trigger change event for any listeners
    selectElement.dispatchEvent(new Event('change', { bubbles: true }));
  }
  
  // Filter teams based on search (including abbreviations)
  function filterTeams(searchTerm) {
    const searchLower = searchTerm.toLowerCase();
    
    // Check if search term matches an abbreviation
    const abbrevMatch = TEAM_ABBREVIATIONS[searchTerm.toUpperCase()];
    
    let filtered = NBA_TEAMS.filter(team => 
      team.toLowerCase().includes(searchLower)
    );
    
    // If abbreviation match found and not already in filtered results, add it
    if (abbrevMatch && !filtered.includes(abbrevMatch)) {
      filtered.unshift(abbrevMatch); // Add to beginning of results
    }
    
    populateDropdown(filtered);
    highlightedIndex = -1;
    
    if (filtered.length > 0) {
      dropdownList.classList.add('show');
    } else {
      dropdownList.classList.remove('show');
    }
  }
  
  // Handle keyboard navigation
  function handleKeyNavigation(e) {
    const items = dropdownList.querySelectorAll('.team-dropdown-item');
    
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        highlightedIndex = Math.min(highlightedIndex + 1, items.length - 1);
        updateHighlight(items);
        break;
        
      case 'ArrowUp':
        e.preventDefault();
        highlightedIndex = Math.max(highlightedIndex - 1, -1);
        updateHighlight(items);
        break;
        
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && items[highlightedIndex]) {
          selectTeam(items[highlightedIndex].dataset.value);
        }
        break;
        
      case 'Escape':
        dropdownList.classList.remove('show');
        highlightedIndex = -1;
        break;
    }
  }
  
  // Update visual highlight
  function updateHighlight(items) {
    items.forEach((item, index) => {
      if (index === highlightedIndex) {
        item.classList.add('highlighted');
        item.scrollIntoView({ block: 'nearest' });
      } else {
        item.classList.remove('highlighted');
      }
    });
  }
  
  // Event listeners
  searchInput.addEventListener('input', (e) => {
    const searchTerm = e.target.value.trim();
    
    if (searchTerm === '') {
      populateDropdown();
      dropdownList.classList.add('show');
    } else {
      filterTeams(searchTerm);
    }
  });
  
  searchInput.addEventListener('focus', () => {
    populateDropdown();
    dropdownList.classList.add('show');
  });
  
  searchInput.addEventListener('keydown', handleKeyNavigation);
  
  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!wrapper.contains(e.target)) {
      dropdownList.classList.remove('show');
      highlightedIndex = -1;
    }
  });
  
  // Initialize with current value
  populateDropdown();
}
