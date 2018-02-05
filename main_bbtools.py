#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      Qiushi
# Created:     06/06/2014

#BBox-Label-Tool
# ===============

# A simple tool for labeling object bounding boxes in images, implemented with Python Tkinter.

# Data Organization
# -----------------
# LabelTool  
# |  
# |--main.py   *# source code for the tool*  
# |  
# |--images/   *# direcotry containing the images to be labeled*  
# |  
# |--labels/original   *# direcotry for the labeling results*  
# |  
# |

# Dependency
# ----------
# python 2.7 win 32bit
# PIL-1.1.7.win32-py2.7

# Startup
# -------
# $ python main.py

# Usage
# -----
# 1. Input a number (e.g, 1, 2, 5...), and click 'Load'. The images along with a few example results will be loaded.
# 2. To create a new bounding box, left-click to select the first vertex. Moving the mouse to draw a rectangle, and left-click again to select the second vertex.
#   - To cancel the bounding box while drawing, just press <Esc>.
#   - To delete a existing bounding box, select it from the listbox, and click 'Delete'.
#   - To delete all existing bounding boxes in the image, simply click 'ClearAll'.
# 3. After finishing one image, click 'Next' to advance. Likewise, click 'Prev' to reverse. Or, input the index and click 'Go' to navigate to an arbitrary image.
#   - The labeling result will be saved if and only if the 'Next' button is clicked.
# #-------------------------------------------------------------------------------
from __future__ import division
from Tkinter import *
import tkMessageBox
from tkFileDialog import askopenfilename
import tkFileDialog
from PIL import Image, ImageTk
import os
import glob
import random

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']

# image sizes for the examples
SIZE = 128, 128

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("Labetool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = TRUE, height = TRUE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category =''
        self.imagename = ''
        self.labelfilename = ''
        self.classLabel = ''
        self.tkimg = None

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text = "Image Dir:")
        self.label.grid(row = 0, column = 0, sticky = E)
        # self.entry = Entry(self.frame)
        # self.entry.grid(row = 0, column = 1, sticky = W+E)

        # self.progLabel = Label(self.frame, text = "Progress:     /    ")
        # self.progLabel.grid(row = 0, column = 2, sticky = W)
        # self.progLabel.pack(side = LEFT, padx = 5)
        
        # self.tmpLabel = Label(self.frame, text = "Go to Image No.")
        # self.tmpLabel.pack(side = LEFT, padx = 5)
        # self.tmpLabel.grid(row = 0, column = 3, sticky = E)

        # self.idxEntry = Entry(self.ctrPanel, width = 5)
        # self.idxEntry.pack(side = LEFT)
        # self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        # self.goBtn.pack(side = LEFT)

        # self.ldBtn = Button(self.frame, text = "Load", command = self.loadDir)
        # self.ldBtn.grid(row = 0, column = 2, sticky = W+E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.config(width=1000, height=800)

        # sbarV = Scrollbar(self.frame, orient=VERTICAL)
        # sbarH = Scrollbar(self.frame, orient=HORIZONTAL)

        # sbarV.config(command=self.mainPanel.yview)
        # sbarH.config(command=self.mainPanel.xview)

        # self.mainPanel.config(yscrollcommand=sbarV.set)
        # self.mainPanel.config(xscrollcommand=sbarH.set)

        # sbarV.pack(side=RIGHT, fill=Y)
        # sbarH.pack(side=BOTTOM, fill=X)

        # self.mainPanel.pack(side=LEFT, expand=YES, fill=BOTH)

        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)

        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("s", self.cancelBBox)
        self.parent.bind("a", self.prevImage) # press 'a' to go backforward
        self.parent.bind("d", self.nextImage) # press 'd' to go forward
        self.mainPanel.grid(row = 1, column = 0, rowspan = 7, columnspan=2, padx=5, pady=5, sticky = W+N)

        # class selection
        self.lb2 = Label(self.frame, text = 'Select Class:')
        self.lb2.grid(row = 1, column = 2,  sticky = W+N)
        self.listbox2 = Listbox(self.frame, width = 42, height = 12)
        self.listbox2.grid(row = 2, column = 2, sticky = N)
        self.listbox2.config(selectmode=EXTENDED)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes:')
        self.lb1.grid(row = 3, column = 2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 42, height = 12)
        self.listbox.grid(row = 4, column = 2, sticky = N)


        self.ctrPanelbtn = Frame(self.frame)
        self.ctrPanelbtn.grid(row = 5, column = 2, sticky = W+E+N)

        self.prevBtn = Button(self.ctrPanelbtn, text='Delete', command = self.delBBox)
        self.prevBtn.pack(side = LEFT, padx = 5)
        # self.prevBtn.grid(row = 5, column = 2, sticky = W+E+N)
        self.nextBtn = Button(self.ctrPanelbtn, text='ClearAll', command = self.clearBBox)
        self.nextBtn.pack(side = LEFT, padx = 5)
        # self.nextBtn.grid(row = 6, column = 2, sticky = W+E+N)


        self.ctrPanelbtnnext = Frame(self.frame)
        self.ctrPanelbtnnext.grid(row = 6, column = 2, sticky = W+E+N)

        self.prevBtn = Button(self.ctrPanelbtnnext, text='<< Prev', command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5)
        # self.prevBtn.grid(row = 5, column = 2, sticky = W+E+N)
        self.nextBtn = Button(self.ctrPanelbtnnext, text='Next >>', command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5)
        # self.nextBtn.grid(row = 6, column = 2, sticky = W+E+N)
        
        #PREVIEW

        # example pannel for illustration
        self.egPanel = Frame(self.frame, border = 3)
        self.egPanel.grid(row = 7, column = 2, rowspan = 3, sticky = N)
        self.tmpLabel2 = Label(self.egPanel, text = "Examples:")
        self.tmpLabel2.pack(side = TOP, padx = 1, pady=1)
        self.egLabels = []
        for i in range(3):
            self.egLabels.append(Label(self.egPanel))
            self.egLabels[-1].pack(side = TOP)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 0, column = 1, columnspan = 2, sticky = W+E+N)
        # self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 10, command = self.prevImage)
        # self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        # self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 10, command = self.nextImage)
        # self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)

        self.entry = Entry(self.ctrPanel)
        self.entry.pack(side = LEFT, padx = 5)

        # self.ldBtn = Button(self.ctrPanel, text = "Load", command = self.loadDir)
        self.ldBtn = Button(self.ctrPanel, text = "Load", command = self.loadDirPop) # popup version
        self.ldBtn.pack(side = LEFT, padx = 5)
        self.imglabel = Label(self.ctrPanel, text = "name:  ")
        self.imglabel.pack(side = LEFT, padx = 5)

        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        # # example pannel for illustration
        # self.egPanel = Frame(self.frame, border = 10)
        # self.egPanel.grid(row = 1, column = 0, rowspan = 7, sticky = N)
        # self.tmpLabel2 = Label(self.egPanel, text = "Examples:")
        # self.tmpLabel2.pack(side = TOP, pady = 5)
        # self.egLabels = []
        # for i in range(3):
        #     self.egLabels.append(Label(self.egPanel))
        #     self.egLabels[-1].pack(side = TOP)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = LEFT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(7, weight = 1)

        # TESTING
        self.initializeClass()


    def initializeClass(self):
        self.className = 'class.txt'

        if os.path.exists(self.className):
            with open(self.className) as f:
                for (i, line) in enumerate(f):
                    self.listbox2.insert(END, '%d %s' % (i, line.split('\n')[0]))


    def loadDirPop(self):
        Tk().withdraw()
        dirname = tkFileDialog.askdirectory(title='Please select a directory')
        self.imageDir = os.path.join(dirname)
        self.imageList= os.listdir(self.imageDir)

        # remove label in dataset
        if 'label' in self.imageList:
            self.imageList.remove('label')
 

        if len(self.imageList) == 0:
            print 'No .JPEG images found in the specified dir!'
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

        # set up output dir
        self.outDir = 'label/'
        if not os.path.exists(self.imageDir + '/label'):
            os.mkdir(self.imageDir + '/label')

        self.tmp = []
        self.egList = []
        self.filelist = []

        # add path
        for i in range (len(self.imageList)):
            file = self.imageDir + '/' + self.imageList[i]
            if not os.path.isdir(file):
                self.filelist.append(os.path.join(self.imageDir,self.imageList[i]))
                # self.filelist.append(file)

        for (i, f) in enumerate(self.filelist):

            im = Image.open(f)

            r = min(SIZE[0] / im.size[0], SIZE[1] / im.size[1])
            new_size = int(r * im.size[0]), int(r * im.size[1])
            self.tmp.append(im.resize(new_size, Image.ANTIALIAS))
            self.egList.append(ImageTk.PhotoImage(self.tmp[-1]))
            print self.egLabels[i], i
            # self.egLabels[i].config(image = self.egList[-1], width = SIZE[0], height = SIZE[1])

        self.loadImage()

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]

        self.img = Image.open(self.imageDir + '/' + imagepath)

        # print self.frame

        # sbarV = Scrollbar(self.frame, orient=VERTICAL)
        # sbarH = Scrollbar(self.frame, orient=HORIZONTAL)
        # # print sbarV, sbarH
        # sbarV.pack(side=RIGHT, fill=Y)
        # sbarH.pack(side=BOTTOM, fill=X)

        # sbarV.config(command=self.mainPanel.yview)
        # sbarH.config(command=self.mainPanel.xview)
        # self.mainPanel.config(yscrollcommand=sbarV.set)
        # self.mainPanel.config(xscrollcommand=sbarH.set)
        # self.mainPanel.pack(side=LEFT, expand=YES, fill=BOTH)

        # self.img = self.img.resize((1280,720), Image.ANTIALIAS)
        self.tkimg = ImageTk.PhotoImage(self.img)
        # self.mainPanel.config(width = max(self.tkimg.width(), 200), height = max(self.tkimg.height(), 200))
        # self.mainPanel.config(width=200, height=200)

        # self.scroll = Scrollbar(self.tkimg)
        # self.mainPanel.configure(yscrollcommand=scroll.set)

        # size_w = int(self.img.size[0])
        # size_h = int(self.img.size[1])


        self.mainPanel.config(width=1000, height=800)

        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)

        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))
        self.imglabel.config(text = "%s" %(os.path.split(imagepath)[-1]))

        # load labels
        self.clearBBox()

        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.imageDir, self.outDir, labelname)
        
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    tmp = [float(t.strip()) for t in line.split()]
                    i, x, y, w, h = [float(t.strip()) for t in line.split()]

                    # chcange tmp into original format rectangle
                    size_w = int(self.img.size[0])
                    size_h = int(self.img.size[1])

                    # input x, y, w, h
                    conv_w = int(w * size_w)
                    conv_h = int(h * size_h)

                    conv_x1 = int((x * size_w) - (conv_w / 2))
                    conv_y1 = int((y * size_h) - (conv_h / 2))

                    conv_x2 = int(conv_w + conv_x1)
                    conv_y2 = int(conv_h + conv_y1)

                    self.bboxList.append(tuple(tmp))
                    tmpId = self.mainPanel.create_rectangle(conv_x1, conv_y1, \
                                                            conv_x2, conv_y2, \
                                                            width = 2, \
                                                            outline = COLORS[(len(self.bboxList)-1) % len(COLORS)])
                    self.bboxIdList.append(tmpId)
                    self.listbox.insert(END, '%d (%0.3f, %0.3f) -> (%0.3f, %0.3f)' %(i, tmp[0], tmp[1], tmp[2], tmp[3]))
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def saveImage(self):
        # label path inside image folder
        if not os.path.exists(self.imageDir + '/label'):
            os.mkdir(self.imageDir + '/label')

        if len(self.bboxList)>0:    
            with open(self.labelfilename, 'w') as f:
                for bbox in self.bboxList:
                    a = str(' '.join(map(str, bbox)) + '\n')
                    if len(a.split(' ')) > 5:
                        # remove if any 'spam' value to txt file
                        a = a.replace(str(self.classLabel) + '.0', "")

                    f.write(a)

        else:
            if os.path.exists(self.labelfilename):
                os.remove(self.labelfilename)


    def mouseClick(self, event):       
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y

        else:  
            sel = self.listbox2.curselection()

            if len(sel) == 0:
                tkMessageBox.showinfo("Alert", "Pilih class terlebih dahulu")
                self.mainPanel.delete(self.bboxId)

            else:
                idx = int(sel[0])

                x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
                y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)   

                # change annonate format
                imagepath = self.imageList[self.cur - 1]
                # im = Image.open(imagepath)
                w = int(self.img.size[0])
                h = int(self.img.size[1])
                size = [w ,h]

                # convert
                w = x2 - x1
                h = y2 - y1
                conv_x = float(x1 + (w / 2)) / float(size[0])
                conv_y = float(y1 + (h / 2)) / float(size[1])
                conv_w = float(w / size[0])
                conf_h = float(h / size[1])

                self.bboxList.append((idx, conv_x, conv_y, conv_w, conf_h))
                self.bboxIdList.append(self.bboxId)
                self.bboxId = None
                self.listbox.insert(END, '%d (%0.4f, %0.4f, %0.4f, %0.4f)' %(idx, conv_x, conv_y, conv_w, conf_h))
                self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
            


        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        self.disp.config(text = 'x: %d, y: %d' %(event.x, event.y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)

        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                            event.x, event.y, \
                                                            width = 2, \
                                                            outline = COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevImage(self, event = None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx and idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()
    
    def add_item():
        listbox1.insert(END, enter1.get())

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.mainloop()