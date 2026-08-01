# Google Stitch / UI Generator Prompt
**Project:** AI-Powered Restaurant Recommendation System Frontend

*Copy and paste the prompt below into Google Stitch (or any AI UI generation tool) to scaffold the frontend.*

***

**System Prompt / Instructions:**

You are an expert frontend developer and UI/UX designer. Your task is to build a high-quality, premium frontend web application for an "AI-Powered Restaurant Recommendation System" (inspired by modern apps like Zomato or Swiggy, but with a highly premium, AI-first aesthetic). 

**Tech Stack:** React (Next.js or Vite), Tailwind CSS, Framer Motion (or CSS animations), and Lucide React (for icons).

### Design & Aesthetic Guidelines
1. **Premium Look & Feel:** Avoid generic, boxy designs. Use a sophisticated, vibrant color palette. Support dark mode by default with deep, rich background colors (e.g., very dark slate or midnight blue) and vibrant accent colors (e.g., coral, electric purple, or neon green for highlights).
2. **Modern Trends:** Incorporate glassmorphism (translucent backgrounds with blur effects) for forms and cards. Use subtle gradients, soft glow effects, and refined drop-shadows to create depth.
3. **Typography:** Use a modern, clean sans-serif font (like Inter, Outfit, or Plus Jakarta Sans). Ensure excellent readability and strong hierarchy.
4. **Micro-animations:** Elements should feel alive. Add smooth hover effects to buttons and cards. Use staggering entry animations when a list of items renders.

### Layout & Component Requirements

The application should have a responsive layout consisting of a **Header**, a **Search/Preference Form**, and a **Results/Recommendations Display Area**.

#### 1. Header
- A sleek navbar featuring an app logo (use a relevant icon) and the title "AI Restaurant Recommender".

#### 2. Preference Form (Input Section)
Design a beautiful, glass-styled form to collect user inputs. It must include:
- **Location:** A styled text input or dropdown with a map pin icon.
- **Budget:** A stylized toggle, segmented control, or styled select dropdown with options: "Low", "Medium", "High".
- **Cuisine:** A text input with a culinary icon.
- **Minimum Rating:** A sleek slider or star-based selector (from 0 to 5).
- **Additional Preferences:** A multi-line text area for free-text AI instructions (e.g., "Must have outdoor seating, family-friendly").
- **Submit Button:** A prominent, glowing or gradient button saying "Get AI Recommendations" with a loading state spinner.

#### 3. Results Section (Output Display)
This area displays the LLM's structured output. 
- **Loading State:** While loading, show premium skeleton loaders that mimic the shape of the recommendation cards with a shimmering effect.
- **Empty State / Error:** A friendly, beautifully illustrated empty state if no restaurants match or if the search hasn't started yet.
- **AI Summary Block:** A highlighted banner at the top of the results that displays a brief summary of the recommendations (e.g., "Here are 3 great Italian spots that match your criteria...").
- **Recommendation Cards:** A grid or list of result cards. Each card MUST include:
  - **Rank Badge:** A stylized badge indicating the rank (e.g., #1, #2).
  - **Restaurant Name & Cuisine:** Displayed prominently.
  - **Rating:** Visual star rating alongside the number (e.g., ⭐ 4.6).
  - **Cost:** Visual cost indicator (e.g., ₹₹₹).
  - **AI Explanation:** A distinct visual section (perhaps with a different background tint and an AI sparkle icon) displaying the 1-2 sentence AI-generated rationale explaining exactly *why* this restaurant was recommended based on the user's specific inputs.

### Responsive Layout (Laptop & Mobile Friendly)
It is absolutely critical that the design looks flawless and functions perfectly on both **laptops/desktops** and **mobile devices** as the primary testing will occur on laptops first. 
- **Laptop/Desktop View:** Utilize the wider screen real-estate. Consider a side-by-side layout (e.g., a sticky left sidebar for the Preference Form and a wider right area for the Results Grid), or a beautifully centered container with the form at the top and results in a responsive grid (2-3 columns).
- **Mobile View:** Ensure everything stacks gracefully into a single column. The form should be compact and easy to scroll past, with results stacking vertically below it. Touch targets (buttons, inputs, sliders) must be large enough for mobile interaction.
- **Fluidity:** Use flexbox, CSS grid, and Tailwind's responsive prefixes (`sm:`, `md:`, `lg:`) to ensure smooth transitions between screen sizes without elements breaking or overflowing.

### Interactivity Requirements
- The form should have clear validation states.
- Cards should slightly elevate and glow on hover.
- Ensure loading spinners and empty states are perfectly centered on all screen sizes.

Please generate the complete, production-ready code for this UI, ensuring all styling is applied via Tailwind CSS and the components are broken down logically.
