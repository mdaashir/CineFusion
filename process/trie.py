import tkinter as tk
from tkinter.messagebox import showinfo

class Node():
    def __init__(self):
        self.child={}
        self.last=False

class Trie():
    lst=[]
    def __init__(self):
        self.root=Node()
       
    def formTrie(self,keys):                                      #Function to access the keys from list and insert it into trie data structure.
        for key in keys:
            self.insert(key)
   
    def insert(self,key):                                         #Insert function:If not present ,inserts key into trie.
        node=self.root                                            #If the key is prefix of trie node, just marks leaf node.
        for a in key:
            if not node.child.get(a):                             #If current character is not present
                node.child[a]=Node()
            node=node.child[a]
        node.last=True                                             
       
    def suggestionRec(self,node,word):
        
        if node.last:
            Trie.lst.append(word)
        for a,n in node.child.items():
            self.suggestionRec(n, word+a)
   
    def printAutoSuggestions(self,key):
        node = self.root
        Trie.lst.clear()
        for a in key:

            if not node.child.get(a):
                return 0
            node = node.child[a]
        if not node.child:
            return -1

        self.suggestionRec(node, key)

        return Trie.lst
    
    
    
keys=[]
file = open("Autocomplete.txt","r")

for word  in file:
    keys.append(word.lower())
    
t1=Trie()
t1.formTrie(keys)                                                 # Calling function of Trie to insert the list of keys into Trie

     
root=tk.Tk()
root.geometry("600x400")                                          # Geometry of the Tkinter frame.
word =tk.StringVar()

def update(data):
    listbox.delete(0,tk.END)
    for item in data:
        listbox.insert(tk.END,item)
        
        
def fillout(event):                
    name_entry.delete(0,tk.END)                                   # Add clicked list item to entry box
    name_entry.insert(0,listbox.get(tk.ACTIVE))
    
    
def check(e):
    String= name_entry.get()                                      # grab what was typed
    if String =="":
        data=keys
    else:
        data=t1.printAutoSuggestions(String)
        
    update(data)

def submit():                                                    # Key To get the searched word and append it History and show a message
    name=word.get()                                              # that the search was successful.                                             
    file=open("BrowserHistory.txt","a")
    file.write(name)
    
    tk.messagebox.showinfo("Autosearch",name + "  Searched Successfully")
    
def view():
    History=[]
    j=0
    file2= open("BrowserHistory.txt","r")
    
    for word in file2:
        History.append(word.lower())
        
    listBox2=tk.Listbox(root,listvariable=History,selectmode = tk.EXTENDED)              # To Display the Browser History in the listbox
    listBox2.grid(row = 2,column = 4)
    
    for i in History:
        listBox2.insert(j+1,History[j])
        j+=1
    listBox2.grid(row = 2,column = 4)
    

name_label = tk.Label(root, text = 'Word list', font=('calibre',10, 'bold'))
name_label.grid(row=0,column=0)

name_entry = tk.Entry(root,textvariable = word, font=('calibre',10,'normal'))             # The entrybox for the user in which he types the word he
name_entry.grid(row=0,column=1)                                                           # wants to search for

vari= tk.Variable(value = keys)
listbox = tk.Listbox(root,listvariable=vari,height = 6,selectmode = tk.EXTENDED)          # Listbox to display all words searched from Trie.
listbox.grid(row = 2,column = 1)

sub_btn=tk.Button(root,text = 'Search', command = submit)                                 # Button when clicked show a pop up box that search
sub_btn.grid(row=10,column=1)                                                             # was successful and append to history when the word is searched

bt=tk.Button(root,text="Browser History",command = view)                                  # Button to view the Browser history
bt.grid(row=11,column=1)


'''def items_selected(event):                                                                #To show a pop-up message.
    selected_indices = listbox.curselection()
    selected_langs = ",".join([listbox.get(i) for i in selected_indices])
    msg = f'You selected: {selected_langs}'
    showinfo(title='Information', message=msg)'''


listbox.bind('<<ListboxSelect>>',fillout)                                                 #To execute a function when the selected items change,
                                                                                          # we bind that function to the <<ListboxSelect>> event
name_entry.bind("<KeyRelease>",check)

root.mainloop()


'''In this project we have used Trie data structure.Using Trie, the key can be searched in O(M) time,where M is the maximum string length
   Trie is basically known for storing some collection of strings and performing efficient search operation on them and also known as prefix Tree'''