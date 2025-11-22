// Reflection View - handles rendering of reflection form

class ReflectionView extends BaseView {
    constructor() {
        super('reflectionContainer');
    }

    // Render reflection form
    renderForm(reflectionData = null) {
        const wentWellEl = document.getElementById('wentWell');
        const doBetterEl = document.getElementById('doBetter');
        const planForWeekEl = document.getElementById('planForWeek');

        if (wentWellEl && reflectionData) {
            wentWellEl.value = reflectionData.wentWell || '';
        }
        if (doBetterEl && reflectionData) {
            doBetterEl.value = reflectionData.doBetter || '';
        }
        if (planForWeekEl && reflectionData) {
            planForWeekEl.value = reflectionData.planForWeek || '';
        }
    }

    // Update form with data
    updateForm(data) {
        const wentWellEl = document.getElementById('wentWell');
        const doBetterEl = document.getElementById('doBetter');
        const planForWeekEl = document.getElementById('planForWeek');

        if (wentWellEl && data.wentWell !== undefined) {
            wentWellEl.value = data.wentWell;
        }
        if (doBetterEl && data.doBetter !== undefined) {
            doBetterEl.value = data.doBetter;
        }
        if (planForWeekEl && data.planForWeek !== undefined) {
            planForWeekEl.value = data.planForWeek;
        }
    }

    // Get form data
    getFormData() {
        const wentWellEl = document.getElementById('wentWell');
        const doBetterEl = document.getElementById('doBetter');
        const planForWeekEl = document.getElementById('planForWeek');

        return {
            wentWell: wentWellEl ? wentWellEl.value : '',
            doBetter: doBetterEl ? doBetterEl.value : '',
            planForWeek: planForWeekEl ? planForWeekEl.value : ''
        };
    }

    // Show validation errors
    showValidationErrors(errors) {
        // Implementation for showing validation errors
        // This would highlight fields with errors
    }

    // Render week title
    renderWeekTitle(weekDates) {
        const titleEl = document.getElementById('reflectionWeekTitle');
        if (titleEl && weekDates) {
            titleEl.textContent = `Week of ${this.formatDate(weekDates.monday)} - ${this.formatDate(weekDates.sunday)}`;
        }
    }
}

// Export for use in other modules
if (typeof window !== 'undefined') {
    window.ReflectionView = ReflectionView;
}

