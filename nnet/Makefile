#
# Toplevel make for neural net implementation.
#
# The source tree is mirrored in the build target obj/.  Binaries are created
# in the same directories as their mains.  Dependencies are stored in the .deps
# toplevel directory, which also mirrors the source tree.
#

CC = g++-4.7
CFLAGS = -std=c++11 -ggdb3 -Wall -Werror -O2

ifdef DEBUG
	CFLAGS += -DDEBUG
endif

SRCDIR = .
OBJDIR = obj
DEPDIR = .deps

SOURCES := $(shell find $(SRCDIR) -name '*.cpp')
HEADERS := $(shell find $(SRCDIR). -name '*.h')

MAINS = $(SRCDIR)/main.cpp

OBJS = $(addprefix $(OBJDIR)/,$(patsubst %.cpp,%.o,$(filter-out $(MAINS),$(SOURCES))))

all: $(OBJS) main tags

define mkbin
$(CC) $^ -o $(subst $(OBJDIR)/,,$(<D))/$@
endef

main: $(OBJDIR)/$(SRCDIR)/main.o $(OBJS); $(mkbin)

$(OBJDIR)/%.o: %.cpp
	@mkdir -p $(@D)
	@mkdir -p $(DEPDIR)/$(<D)
	$(CC) $(CFLAGS) -MMD -MP -MF $(DEPDIR)/$(<:.cpp=.d) -c $< -o $@

tags: $(SOURCES) $(HEADERS)
	ctags -R

clean:
	-rm -rf $(DEPDIR) $(OBJDIR) $(SRCDIR)/main

.PHONY: all clean tags
