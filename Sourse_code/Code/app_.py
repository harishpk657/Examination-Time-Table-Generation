import pandas as pd  # Import pandas for data manipulation and analysis
import streamlit as st  # Import Streamlit for creating the interactive web application
from io import BytesIO  # Import BytesIO to handle in-memory file operations

# Function to create a seating arrangement for a room
def create_seating_arrangement(room, invigilator):
    room_no = room['Room No']  # Get the room number
    students = [student[1] for student in room['Assigned Students']]  # Extract student roll numbers
    total_students = len(students)  # Calculate the total number of students

    # Calculate number of rows needed for 4 columns
    rows = (total_students + 3) // 4  # Divide students into rows for a 4-column layout

    # Create seating grid
    seating_grid = []  # Initialize an empty seating grid
    for i in range(rows):  # Iterate through each row
        seating_row = []  # Initialize an empty row
        for col in range(4):  # Iterate through each column
            index = i + col * rows  # Calculate the index of the student for the current cell
            if index < total_students:  # If the index is within the total students
                seating_row.append(students[index])  # Add the student to the row
            else:
                seating_row.append('')  # Add an empty seat if no student is available
        seating_grid.append(seating_row)  # Append the completed row to the seating grid

    # Convert the seating grid to a DataFrame
    seating_df = pd.DataFrame(seating_grid)

    # Add room number and invigilator info on top
    seating_df = pd.concat([
        pd.DataFrame([[f"Room: {room_no}", f"Invigilator: {invigilator}", '', '']]),  # Add header row
        seating_df  # Append the seating grid
    ], ignore_index=True)

    return seating_df  # Return the seating arrangement as a DataFrame

# Streamlit App configuration and title
st.set_page_config(layout="wide")  # Set the layout to wide for better visualization
st.title("Exam Timetable Generator")  # Set the application title

# Sidebar for file uploads
st.sidebar.header("Upload Files")  # Sidebar header
faculty_file = st.sidebar.file_uploader("Upload Faculty.csv", type="csv")  # Upload faculty file
room_capacity_file = st.sidebar.file_uploader("Upload RoomCapacity.csv", type="csv")  # Upload room capacity file
students_file = st.sidebar.file_uploader("Upload Students.csv", type="csv")  # Upload students file

if faculty_file and room_capacity_file and students_file:  # Check if all files are uploaded
    # Initialize session state for navigation
    if 'page' not in st.session_state:
        st.session_state.page = 'buttons'  # Set default page to buttons
    if 'seating_room_list' not in st.session_state:
        st.session_state.seating_room_list = []  # Initialize room list for seating navigation

    # Function to navigate to the seating arrangement list
    def go_to_seating_list():
        st.session_state.page = 'seating_list'  # Change page to seating list

    # Function to navigate back to the main buttons
    def go_to_buttons():
        st.session_state.page = 'buttons'  # Change page to buttons

    # Main Buttons for Report Generation
    if st.session_state.page == 'buttons':  # If the current page is the buttons page
        timetable_button = st.button("Generate Updated Exam Timetable")  # Button to generate timetable
        summary_button = st.button("Generate Room Summary Report")  # Button to generate room summary
        seating_button = st.button("Generate Room-wise Seating Arrangements", on_click=go_to_seating_list)  # Button to go to seating arrangements

        # Read uploaded files into DataFrames
        faculty_df = pd.read_csv(faculty_file)  # Faculty data
        room_capacity_df = pd.read_csv(room_capacity_file)  # Room capacity data
        students_df = pd.read_csv(students_file)  # Students data

        # Prepare a round-robin arrangement of students from all branches
        students_combined = []  # Initialize list for combined student roll numbers
        branch_columns = students_df.columns  # Get branch columns
        num_rows = students_df.shape[0]  # Get number of rows in student data

        for i in range(num_rows):  # Iterate through each student row
            for branch in branch_columns:  # Iterate through each branch
                if not pd.isna(students_df.loc[i, branch]):  # Check if roll number exists
                    students_combined.append((branch, students_df.loc[i, branch]))  # Add student to combined list

        # Assign students to rooms based on capacity
        room_assignment = []  # Initialize list for room assignments
        start_index = 0  # Start index for assigning students

        for _, row in room_capacity_df.iterrows():  # Iterate through each room
            room_no = row['Room No']  # Room number
            capacity = row['Capacity']  # Room capacity
            assigned_students = students_combined[start_index:start_index + capacity]  # Students assigned to room
            if assigned_students:  # Check if room is not empty
                room_assignment.append({
                    'Room No': room_no,
                    'Assigned Students': assigned_students,
                    'Total Students': len(assigned_students)
                })
            start_index += capacity  # Update start index for next room

        # Assign invigilators to rooms
        invigilator_count = len(faculty_df)  # Total number of invigilators
        for i, room in enumerate(room_assignment):  # Assign invigilator to each room
            room['Invigilator'] = faculty_df.iloc[i % invigilator_count]['Faculty']

        # Generate Updated Exam Timetable
        if timetable_button:  # If timetable button is clicked
            output_df = pd.DataFrame(room_assignment)  # Convert room assignments to DataFrame
            st.subheader("Updated Exam Timetable")  # Display header
            st.dataframe(output_df)  # Show timetable

            timetable_csv = BytesIO()  # Create in-memory file
            output_df.to_csv(timetable_csv, index=False)  # Save timetable to file
            timetable_csv.seek(0)  # Reset file pointer

            st.download_button("Download Updated Exam Timetable", timetable_csv, "Updated_Exam_Timetable.csv", "text/csv")  # Download button

        # Generate Room Summary Report
        if summary_button:  # If summary button is clicked
            room_summary = []  # Initialize room summary list
            for room in room_assignment:  # Iterate through each room
                room_no = room['Room No']  # Room number
                assigned_students = room['Assigned Students']  # Assigned students
                branch_mapping = {}  # Map branches to students
                for branch, student in assigned_students:  # Assign students to branches
                    if branch not in branch_mapping:
                        branch_mapping[branch] = []
                    branch_mapping[branch].append(student)

                # Create ranges for branches
                ranges = [f"{students[0]} - {students[-1]}" for students in branch_mapping.values()]
                room_summary.append({
                    'Room No': room_no,
                    'Ranges': "\n".join(ranges),
                    'Total Students': len(assigned_students)
                })

            room_summary_df = pd.DataFrame(room_summary)  # Convert to DataFrame
            st.subheader("Room Summary Report")  # Display header
            st.dataframe(room_summary_df)  # Show summary

            summary_csv = BytesIO()  # Create in-memory file
            room_summary_df.to_csv(summary_csv, index=False)  # Save summary to file
            summary_csv.seek(0)  # Reset file pointer

            st.download_button("Download Room Summary Report", summary_csv, "Room_Summary_Report.csv", "text/csv")  # Download button

        # Save seating room list for navigation
        st.session_state.seating_room_list = room_assignment  # Save room list

    # Generate Room-wise Seating Arrangements
    elif st.session_state.page == 'seating_list':  # If the page is seating list
        st.button("Back to Main Menu", on_click=go_to_buttons)  # Button to go back to main menu

        st.subheader("Select a Room to View and Download Seating Arrangement")  # Display header
        for room in st.session_state.seating_room_list:  # Iterate through each room
            room_no = room['Room No']  # Room number
            invigilator = room['Invigilator']  # Invigilator
            if st.button(f"Generate Seating Arrangement for {room_no}"):  # Button for each room
                seating_df = create_seating_arrangement(room, invigilator)  # Generate seating arrangement

                seating_file = BytesIO()  # Create in-memory file
                with pd.ExcelWriter(seating_file, engine='xlsxwriter') as writer:  # Write to Excel file
                    seating_df.to_excel(writer, index=False, header=False, sheet_name='Seating Arrangement')
                seating_file.seek(0)  # Reset file pointer

                st.download_button(  # Download button
                    f"Download Seating Arrangement for {room_no}",
                    seating_file,
                    f"Seating_Arrangement_{room_no}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.success(f"Seating Arrangement for {room_no} Generated Successfully!")  # Success message
